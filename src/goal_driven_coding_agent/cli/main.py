"""Command-line entry point for the goal-driven coding agent."""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from dotenv import load_dotenv

from goal_driven_coding_agent.agents.types import (
    GoalDrivenAgentConfig,
    GoalDrivenAgentResult,
    McpRuntimeConfig,
)
from goal_driven_coding_agent.agents.coding.runner import (
    GoalDrivenAgentExecutionError,
    GoalDrivenCodingAgentRunner,
)

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_TIMEOUT_SECONDS = 1200
DEFAULT_MODEL = "gpt-4o-mini"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGGER = logging.getLogger("goal_driven_coding_agent")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run the goal-driven coding agent on a specific goal.",
    )
    parser.add_argument("--goal", type=str, required=True, help="Goal description.")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help="Maximum agent loop iterations.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Global timeout in seconds for the run.",
    )
    parser.add_argument(
        "--sandbox-root",
        type=Path,
        default=PROJECT_ROOT / "sandbox_volumes",
        help="Directory where sandbox volumes are stored.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Model identifier passed to the OpenAI Agents SDK.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Optional identifier for the run. Generated when omitted.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity.",
    )
    parser.add_argument(
        "--mcp-compose-file",
        type=Path,
        default=PROJECT_ROOT / "containers/docker-compose.mcp.yaml",
        help="Path to the docker-compose file for MCP servers.",
    )
    parser.add_argument(
        "--mcp-project-name",
        type=str,
        default=None,
        help="Docker Compose project name (defaults to run-specific identifier).",
    )
    parser.add_argument(
        "--filesystem-server-url",
        type=str,
        default="http://127.0.0.1:7101/mcp",
        help="Public URL of the filesystem MCP server.",
    )
    parser.add_argument(
        "--executor-server-url",
        type=str,
        default="http://127.0.0.1:7102/mcp",
        help="Public URL of the executor MCP server.",
    )
    return parser.parse_args(argv)


def _configure_logging(log_level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def _load_env() -> None:
    dotenv_path = PROJECT_ROOT / ".env"
    if dotenv_path.exists():
        try:
            load_dotenv(dotenv_path=dotenv_path, override=False)
        except PermissionError as exc:  # pragma: no cover - filesystem guard
            LOGGER.warning("Unable to read .env file (%s). Continuing without it.", exc)


def _require_environment_variable(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Environment variable {name} is required but not set. "
            "Ensure your .env file is populated."
        )
    return value


def _generate_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{timestamp}-{uuid.uuid4().hex[:8]}"


def _build_config(args: argparse.Namespace) -> GoalDrivenAgentConfig:
    sandbox_root = (args.sandbox_root or PROJECT_ROOT / "sandbox_volumes").expanduser()
    sandbox_root.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or _generate_run_id()
    project_name = _sanitize_compose_project(args.mcp_project_name or f"gdc-mcp-{run_id}")
    mcp_config = McpRuntimeConfig(
        compose_file=args.mcp_compose_file.resolve(),
        project_name=project_name,
        filesystem_server_url=args.filesystem_server_url,
        executor_server_url=args.executor_server_url,
        auto_start=False,
    )
    return GoalDrivenAgentConfig(
        goal=args.goal.strip(),
        workspace_root=PROJECT_ROOT,
        sandbox_root=sandbox_root,
        model=args.model,
        max_iterations=args.max_iterations,
        timeout_seconds=args.timeout_seconds,
        run_id=run_id,
        mcp=mcp_config,
    )


def _sanitize_compose_project(name: str) -> str:
    sanitized = re.sub(r"[^a-z0-9_-]", "-", name.lower())
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    if not sanitized:
        return "gdc-mcp"
    if not sanitized[0].isalnum():
        sanitized = f"gdc-{sanitized}"
    return sanitized


def _print_result_summary(result: GoalDrivenAgentResult) -> None:
    LOGGER.info(
        (
            "Run %s finished with success=%s in %.2fs over %s iterations. "
            "Sandbox: %s | Final output: %s"
        ),
        result.run_id,
        result.success,
        result.duration_seconds,
        result.iterations,
        result.sandbox_path,
        (result.final_output or "N/A"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args(argv)
    _configure_logging(args.log_level)
    LOGGER.debug("CLI arguments parsed: %s", args)

    _load_env()
    _require_environment_variable("OPENAI_API_KEY")

    config = _build_config(args)
    runner = GoalDrivenCodingAgentRunner()

    try:
        result = runner.run(config)
    except GoalDrivenAgentExecutionError as exc:
        LOGGER.error("Agent pipeline failed to complete: %s", exc)
        return 2
    except Exception:  # pragma: no cover - defensive logging
        LOGGER.exception("Agent execution failed unexpectedly.")
        return 1

    _print_result_summary(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

