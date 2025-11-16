"""Run manifest recording for tracing agent activity."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agents.items import ItemHelpers, MCPListToolsItem, RunItem, ToolCallItem
from agents.lifecycle import RunHooks
from agents.run_context import RunContextWrapper
from agents.tool import Tool
from openai.types.responses.response_output_item import McpCall

from goal_driven_coding_agent.agents.types import GoalDrivenAgentConfig, GoalDrivenAgentResult
from agents.result import RunResult


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _truncate(value: str | None, *, limit: int = 400) -> str | None:
    if value is None:
        return None
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


@dataclass(slots=True)
class RunManifestRecorder:
    """Collects structured telemetry for a single agent run."""

    config: GoalDrivenAgentConfig
    sandbox_path: Path
    start_time: datetime = field(default_factory=_utcnow)
    events: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    _current_llm_event: dict[str, Any] | None = field(default=None, init=False)
    _sequence_counter: int = field(default=0, init=False)
    _iterations: int = field(default=0, init=False)
    data: dict[str, Any] | None = field(default=None, init=False)

    def log_llm_start(
        self,
        *,
        system_prompt: str | None,
        input_items: list[Any],
    ) -> None:
        self._iterations += 1
        event = {
            "type": "llm_call",
            "sequence": self._next_sequence(),
            "iteration": self._iterations,
            "started_at": _utcnow().isoformat(),
            "system_prompt_preview": _truncate(system_prompt, limit=600),
            "input_preview": _truncate(self._summarize_input_items(input_items), limit=600),
        }
        self.events.append(event)
        self._current_llm_event = event

    def log_llm_end(self, *, response: Any) -> None:
        if not self._current_llm_event:
            return
        event = self._current_llm_event
        event["ended_at"] = _utcnow().isoformat()
        event["response_id"] = response.response_id
        event["response_summary"] = _truncate(self._summarize_response(response), limit=800)
        if getattr(response, "usage", None):
            usage = response.usage
            event["usage"] = {
                "total_tokens": getattr(usage, "total_tokens", None),
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
            }
        self._current_llm_event = None

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def finalize_success(self, *, result: GoalDrivenAgentResult, raw_run: RunResult) -> None:
        self._capture_run_items(result.run_id, raw_run.new_items)
        self.data = {
            "run_id": result.run_id,
            "goal": self.config.goal,
            "model": self.config.model,
            "sandbox_path": str(result.sandbox_path),
            "started_at": self.start_time.isoformat(),
            "completed_at": _utcnow().isoformat(),
            "duration_seconds": (_utcnow() - self.start_time).total_seconds(),
            "iterations": self._iterations,
            "success": result.success,
            "final_output": result.final_output,
            "events": self.events,
            "errors": self.errors + list(result.errors),
        }

    def finalize_failure(self, *, error_message: str) -> None:
        self.add_error(error_message)
        now = _utcnow()
        self.data = {
            "run_id": self.config.run_id if hasattr(self.config, "run_id") else "unknown-run",
            "goal": self.config.goal,
            "model": self.config.model,
            "sandbox_path": str(self.sandbox_path),
            "started_at": self.start_time.isoformat(),
            "completed_at": now.isoformat(),
            "duration_seconds": (now - self.start_time).total_seconds(),
            "iterations": self._iterations,
            "success": False,
            "final_output": None,
            "events": self.events,
            "errors": self.errors,
        }

    def persist(self) -> Path:
        if self.data is None:
            raise RuntimeError("Manifest cannot be persisted before finalize() is called.")
        manifest_path = self.sandbox_path / "run_manifest.json"
        manifest_path.write_text(json.dumps(self.data, indent=2))
        return manifest_path

    def _capture_run_items(
        self,
        run_id: str,
        items: Sequence[RunItem],
    ) -> None:
        for item in items:
            if isinstance(item, ToolCallItem):
                raw = item.raw_item
                if isinstance(raw, McpCall):
                    self.events.append(
                        {
                            "type": "mcp_call",
                            "sequence": self._next_sequence(),
                            "server_label": raw.server_label,
                            "tool_name": raw.name,
                            "arguments": self._safe_json(raw.arguments),
                            "status": raw.status,
                            "output_preview": _truncate(raw.output, limit=600),
                            "error": raw.error,
                        }
                    )
            elif isinstance(item, MCPListToolsItem):
                raw = item.raw_item
                self.events.append(
                    {
                        "type": "mcp_list_tools",
                        "sequence": self._next_sequence(),
                        "server_label": raw.server_label,
                        "tool_count": len(raw.tools),
                    }
                )

    def _summarize_input_items(self, items: list[Any]) -> str:
        snippets: list[str] = []
        for entry in items:
            content = entry.get("content") if isinstance(entry, dict) else None
            if isinstance(content, str):
                snippets.append(content)
            elif isinstance(content, list):
                for block in content:
                    text = block.get("text") if isinstance(block, dict) else None
                    if text:
                        snippets.append(text)
        return " ".join(snippets).strip()

    def _summarize_response(self, response: Any) -> str:
        texts: list[str] = []
        for output in response.output:
            snippet = ItemHelpers.extract_last_text(output)
            if snippet:
                texts.append(snippet)
        return " ".join(texts).strip()

    def _safe_json(self, raw: str) -> Any:
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def _next_sequence(self) -> int:
        self._sequence_counter += 1
        return self._sequence_counter


class ManifestRunHooks(RunHooks):
    """Run hooks that forward lifecycle events to the manifest recorder."""

    def __init__(self, recorder: RunManifestRecorder) -> None:
        self.recorder = recorder

    async def on_llm_start(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        system_prompt: str | None,
        input_items: list[Any],
    ) -> None:
        self.recorder.log_llm_start(system_prompt=system_prompt, input_items=input_items)

    async def on_llm_end(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        response: Any,
    ) -> None:
        self.recorder.log_llm_end(response=response)

    async def on_tool_start(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        tool: Tool,
    ) -> None:
        self.recorder.events.append(
            {
                "type": "local_tool_start",
                "sequence": self.recorder._next_sequence(),
                "tool_name": getattr(tool, "name", repr(tool)),
                "timestamp": _utcnow().isoformat(),
            }
        )

    async def on_tool_end(
        self,
        context: RunContextWrapper[Any],
        agent: Agent[Any],
        tool: Tool,
        result: str,
    ) -> None:
        self.recorder.events.append(
            {
                "type": "local_tool_end",
                "sequence": self.recorder._next_sequence(),
                "tool_name": getattr(tool, "name", repr(tool)),
                "timestamp": _utcnow().isoformat(),
                "result_preview": _truncate(result, limit=600),
            }
        )

