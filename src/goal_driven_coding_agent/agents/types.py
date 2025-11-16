"""Shared dataclasses used across agent runners."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class GoalDrivenAgentConfig:
    """Immutable configuration describing a single coding agent run."""

    goal: str
    workspace_root: Path
    sandbox_root: Path
    model: str
    max_iterations: int
    timeout_seconds: int
    run_id: str
    mcp: "McpRuntimeConfig"
    context_blocks: Sequence[str] = field(default_factory=tuple)

    def resolve_sandbox_path(self) -> Path:
        """Return the absolute sandbox path for this run."""
        sandbox_path = self.sandbox_root / self.run_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        return sandbox_path


@dataclass(slots=True)
class GoalDrivenAgentResult:
    """Structured result emitted after a coding agent finishes."""

    goal: str
    run_id: str
    success: bool
    iterations: int
    started_at: datetime
    finished_at: datetime
    sandbox_path: Path
    final_output: str | None = None
    logs: Sequence[str] = field(default_factory=list)
    errors: Sequence[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """Convenience accessor returning execution duration."""
        return (self.finished_at - self.started_at).total_seconds()


def build_default_result(
    config: GoalDrivenAgentConfig,
    *,
    success: bool = False,
    iterations: int = 0,
    logs: Sequence[str] | None = None,
    errors: Sequence[str] | None = None,
) -> GoalDrivenAgentResult:
    """Create a result placeholder for early-return scenarios."""
    now = datetime.now(timezone.utc)
    return GoalDrivenAgentResult(
        goal=config.goal,
        run_id=config.run_id,
        success=success,
        iterations=iterations,
        started_at=now,
        finished_at=now,
        sandbox_path=config.resolve_sandbox_path(),
        final_output=None,
        logs=list(logs) if logs else [],
        errors=list(errors) if errors else [],
    )


@dataclass(slots=True)
class McpRuntimeConfig:
    """Configuration describing how to reach MCP servers for a run."""

    compose_file: Path
    project_name: str
    filesystem_server_url: str
    executor_server_url: str
    auto_start: bool = True

