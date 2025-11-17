"""Goal-driven coding agent runner implementation."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Sequence
import json

from agents import Agent
from agents.mcp import MCPServer, MCPServerStreamableHttp, MCPServerStreamableHttpParams
from agents.run import RunResult, Runner

from goal_driven_coding_agent.agents.base import AgentRunner
from goal_driven_coding_agent.agents.types import (
    GoalDrivenAgentConfig,
    GoalDrivenAgentResult,
)
from goal_driven_coding_agent.telemetry import ManifestRunHooks, RunManifestRecorder

logger = logging.getLogger(__name__)


class GoalDrivenAgentExecutionError(RuntimeError):
    """Raised when the coding agent execution fails."""


@dataclass(slots=True)
class GoalDrivenCodingAgentRunner(AgentRunner):
    """Coordinates the OpenAI Agents SDK, MCP tools, and sandbox lifecycle."""

    def run(self, config: GoalDrivenAgentConfig) -> GoalDrivenAgentResult:
        """Execute the goal-driven coding agent using MCP servers."""
        return asyncio.run(self._run_async(config))

    async def _run_async(self, config: GoalDrivenAgentConfig) -> GoalDrivenAgentResult:
        logger.info("Starting goal-driven coding agent", extra={"run_id": config.run_id})
        started_at = datetime.now(timezone.utc)
        sandbox_path = config.resolve_sandbox_path()
        logger.debug("Sandbox prepared at %s", sandbox_path)
        recorder = RunManifestRecorder(config=config, sandbox_path=sandbox_path)
        hooks = ManifestRunHooks(recorder)

        mcp_servers = self._build_mcp_servers(config)
        await self._connect_mcp_servers(mcp_servers)
        agent = self._build_agent(config, mcp_servers)

        try:
            run_result = await Runner.run(
                starting_agent=agent,
                input=self._build_agent_input(config),
                max_turns=config.max_iterations,
                hooks=hooks,
            )
        except Exception as exc:  # pragma: no cover - LLM invocation guard
            logger.exception("Agent execution failed.")
            recorder.finalize_failure(error_message=str(exc))
            manifest_path = recorder.persist()
            logger.info("Run manifest recorded at %s (failure)", manifest_path)
            raise GoalDrivenAgentExecutionError(str(exc)) from exc
        finally:
            await self._cleanup_mcp_servers(mcp_servers)

        result = self._build_result(
            config=config,
            run_result=run_result,
            started_at=started_at,
            sandbox_path=sandbox_path,
        )
        recorder.finalize_success(result=result, raw_run=run_result)
        manifest_path = recorder.persist()
        logger.info(
            "Agent completed run %s with success=%s",
            result.run_id,
            result.success,
        )
        logger.info("Run manifest recorded at %s", manifest_path)
        return result

    def _build_agent(self, config: GoalDrivenAgentConfig, mcp_servers: Sequence[MCPServer]) -> Agent[Any]:
        return Agent(
            name="GoalDrivenCoder",
            instructions=self._agent_instructions(config),
            mcp_servers=list(mcp_servers),
            model=config.model,
        )

    def _build_agent_input(self, config: GoalDrivenAgentConfig) -> str:
        sandbox_path = config.sandbox_root / config.run_id
        base = (
            "You are assigned a new coding mission.\n"
            f"Goal: {config.goal}\n"
            f"Sandbox root: {sandbox_path}\n"
            "All filesystem operations MUST remain inside this directory. "
            "Use relative paths without leading slashes (e.g. `bubble_sort.py` or "
            "`src/tests/test_sort.py`). Never reference host filesystem paths such as `/Users/...`.\n"
            "Plan your steps, produce code, run the necessary verification commands, "
            "and declare success only after verification passes."
        )
        if not config.context_blocks:
            return base
        context = "\n\n".join(
            f"[Context {index}] {block}"
            for index, block in enumerate(config.context_blocks, start=1)
        )
        return f"{base}\n\nAdditional reference material (read-only):\n{context}"

    def _agent_instructions(self, config: GoalDrivenAgentConfig) -> str:
        sandbox_path = config.sandbox_root / config.run_id
        return (
            "You are an autonomous, goal-driven coding agent.\n"
            "1. Follow the workflow described in the goal to implement the solution.\n"
            "2. Use the provided tools to read, write, and test your code.\n"
            "3. Pay close attention to the `exit_code` from the `sandbox_run_command` tool.\n"
            "4. If the `exit_code` is `0`, all tests have passed. Your job is done. Do not call any more tools. Respond with a final, brief message declaring success (e.g., 'All tests passed. Goal achieved.').\n"
            "5. If the tests fail, analyze the output, refine your code, and try again.\n"
            f"IMPORTANT: All file operations must be within the sandbox root: {sandbox_path}. Use relative paths."
        )

    def _build_mcp_servers(self, config: GoalDrivenAgentConfig) -> list[MCPServer]:
        return [
            MCPServerStreamableHttp(
                params=MCPServerStreamableHttpParams(url=config.mcp.filesystem_server_url),
                name="sandbox-filesystem",
                cache_tools_list=True,
            ),
            MCPServerStreamableHttp(
                params=MCPServerStreamableHttpParams(url=config.mcp.executor_server_url),
                name="sandbox-executor",
                cache_tools_list=True,
            ),
        ]

    def _build_result(
        self,
        *,
        config: GoalDrivenAgentConfig,
        run_result: RunResult,
        started_at: datetime,
        sandbox_path: Any,
    ) -> GoalDrivenAgentResult:
        finished_at = datetime.now(timezone.utc)
        final_output = str(run_result.final_output) if run_result.final_output else None
        logs: Sequence[str] = [
            str(item) for item in getattr(run_result, "new_items", [])
        ]
        success = self._tests_passed(run_result=run_result, fallback=bool(final_output))
        return GoalDrivenAgentResult(
            goal=config.goal,
            run_id=config.run_id,
            success=success,
            iterations=len(run_result.new_items),
            started_at=started_at,
            finished_at=finished_at,
            sandbox_path=sandbox_path,
            final_output=final_output,
            logs=logs,
            errors=[],
        )

    def _tests_passed(self, run_result: RunResult, fallback: bool) -> bool:
        """Determine success based on the latest pytest run, if available.

        We scan MCP tool calls from the sandbox executor for `sandbox_run_command`
        invocations that executed pytest, and then derive success from the most
        recent pytest exit code. When no such run can be found or parsed, we
        fall back to the provided default.
        """
        try:
            # Local imports avoid hard dependencies at module import time.
            from agents.items import ToolCallItem  # type: ignore
            from openai.types.responses.response_output_item import McpCall  # type: ignore
        except Exception:  # pragma: no cover - defensive import guard
            return fallback

        last_pytest_exit: int | None = None

        for item in getattr(run_result, "new_items", []):
            if not isinstance(item, ToolCallItem):
                continue
            raw = getattr(item, "raw_item", None)
            if not isinstance(raw, McpCall):
                continue
            if raw.server_label != "sandbox-executor" or raw.name != "sandbox_run_command":
                continue

            try:
                payload = json.loads(raw.output)
            except Exception:
                continue

            command = payload.get("command")
            if isinstance(command, list):
                command_str = " ".join(str(part) for part in command)
            else:
                command_str = str(command or "")

            if "pytest" not in command_str:
                continue

            exit_code = payload.get("exit_code")
            if isinstance(exit_code, int):
                last_pytest_exit = exit_code

        if last_pytest_exit is None:
            return fallback
        return last_pytest_exit == 0

    async def _connect_mcp_servers(self, servers: Sequence[MCPServer]) -> None:
        for server in servers:
            await self._connect_single_server(server)

    async def _connect_single_server(self, server: MCPServer) -> None:
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                await server.connect()
                return
            except Exception as exc:  # pragma: no cover - transport timing
                if attempt == max_attempts:
                    logger.error("Failed to connect to MCP server %s: %s", server.name, exc)
                    raise
                logger.warning(
                    "MCP server %s connection attempt %s/%s failed: %s",
                    server.name,
                    attempt,
                    max_attempts,
                    exc,
                )
                await asyncio.sleep(min(1.0 * attempt, 5.0))

    async def _cleanup_mcp_servers(self, servers: Sequence[MCPServer]) -> None:
        for server in servers:
            try:
                await self._cleanup_single_server(server)
            except asyncio.CancelledError:
                logger.warning("Cleanup for MCP server %s cancelled; suppressing.", server.name)

    async def _cleanup_single_server(self, server: MCPServer) -> None:
        try:
            await server.cleanup()
        except asyncio.CancelledError:  # pragma: no cover - generator shutdown races
            logger.warning("MCP server %s cleanup cancelled; continuing.", server.name)
        except Exception as exc:  # pragma: no cover - best effort cleanup
            logger.warning("Error while cleaning up MCP server %s: %s", server.name, exc)

