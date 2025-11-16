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
from goal_driven_coding_agent.benchmarks import (
    BenchmarkDiscoveryError,
    BenchmarkExercise,
    BenchmarkSuiteLoader,
    materialize_benchmark_exercise,
)

DEFAULT_MAX_ITERATIONS = 10
DEFAULT_TIMEOUT_SECONDS = 1200
DEFAULT_MODEL = "gpt-4o-mini"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGGER = logging.getLogger("goal_driven_coding_agent")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Run the goal-driven coding agent on a specific goal or benchmark suite.",
    )
    goal_group = parser.add_mutually_exclusive_group(required=True)
    goal_group.add_argument("--goal", type=str, help="Goal description.")
    goal_group.add_argument(
        "--benchmarks",
        action="store_true",
        help="Solve Polyglot Benchmark exercises sequentially.",
    )
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
    parser.add_argument(
        "--benchmarks-limit",
        type=int,
        default=None,
        help="Run only the first N exercises (requires --benchmarks).",
    )
    args = parser.parse_args(argv)
    if args.benchmarks_limit is not None and not args.benchmarks:
        parser.error("--benchmarks-limit can only be used with --benchmarks.")
    return args


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


def _resolve_sandbox_root(args: argparse.Namespace) -> Path:
    return (args.sandbox_root or PROJECT_ROOT / "sandbox_volumes").expanduser()


def _build_config(
    args: argparse.Namespace,
    *,
    goal: str,
    run_id: str | None = None,
    context_blocks: Sequence[str] | None = None,
) -> GoalDrivenAgentConfig:
    sandbox_root = _resolve_sandbox_root(args)
    sandbox_root.mkdir(parents=True, exist_ok=True)
    final_run_id = run_id or args.run_id or _generate_run_id()
    project_name = _sanitize_compose_project(
        args.mcp_project_name or f"gdc-mcp-{final_run_id}"
    )
    mcp_config = McpRuntimeConfig(
        compose_file=args.mcp_compose_file.resolve(),
        project_name=project_name,
        filesystem_server_url=args.filesystem_server_url,
        executor_server_url=args.executor_server_url,
        auto_start=False,
    )
    return GoalDrivenAgentConfig(
        goal=goal.strip(),
        workspace_root=PROJECT_ROOT,
        sandbox_root=sandbox_root,
        model=args.model,
        max_iterations=args.max_iterations,
        timeout_seconds=args.timeout_seconds,
        run_id=final_run_id,
        mcp=mcp_config,
        context_blocks=tuple(context_blocks or ()),
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

    if args.benchmarks:
        return _run_benchmarks(args)
    return _run_single_goal(args)


def _run_single_goal(args: argparse.Namespace) -> int:
    """Execute a single goal provided via CLI."""
    config = _build_config(args, goal=args.goal or "")
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


def _run_benchmarks(args: argparse.Namespace) -> int:
    """Execute Polyglot Benchmark exercises sequentially."""
    sandbox_root = _resolve_sandbox_root(args)
    loader = BenchmarkSuiteLoader(sandbox_root)
    try:
        exercises = loader.discover(limit=args.benchmarks_limit)
    except (BenchmarkDiscoveryError, ValueError) as exc:
        LOGGER.error("Unable to load benchmark exercises: %s", exc)
        return 2

    if not exercises:
        LOGGER.warning("No benchmark exercises found in %s", loader.practice_root)
        return 0

    base_run_id = args.run_id or _generate_run_id()
    runner = GoalDrivenCodingAgentRunner()
    successes = 0
    failures = 0

    for index, seed_exercise in enumerate(exercises, start=1):
        run_id = f"{base_run_id}-{seed_exercise.slug}"
        LOGGER.info(
            "Starting benchmark %s/%s: %s",
            index,
            len(exercises),
            seed_exercise.display_name,
        )
        run_path = sandbox_root / run_id
        run_path.mkdir(parents=True, exist_ok=True)
        run_exercise = materialize_benchmark_exercise(seed_exercise, run_path)
        context_blocks = run_exercise.build_context_blocks()
        config = _build_config(
            args,
            goal=run_exercise.build_goal(),
            run_id=run_id,
            context_blocks=context_blocks,
        )
        _log_read_only_seed_warning(seed_exercise, run_exercise)
        try:
            result = runner.run(config)
        except GoalDrivenAgentExecutionError as exc:
            LOGGER.error("Benchmark %s failed to execute: %s", seed_exercise.slug, exc)
            failures += 1
            continue
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.exception("Benchmark %s crashed unexpectedly.", seed_exercise.slug)
            failures += 1
            continue

        _print_result_summary(result)
        if result.success:
            successes += 1
        else:
            failures += 1

    LOGGER.info(
        "Benchmark suite finished with %s successes and %s failures.",
        successes,
        failures,
    )
    return 0 if failures == 0 else 3


def _log_read_only_seed_warning(
    seed_exercise: BenchmarkExercise, run_exercise: BenchmarkExercise
) -> None:
    LOGGER.info(
        "Copied benchmark %s into %s. Treat the original seed directory "
        "`sandbox_volumes/benchmarks/.../%s` as read-only; persist all edits under %s.",
        seed_exercise.slug,
        run_exercise.relative_directory,
        seed_exercise.relative_directory,
        run_exercise.relative_directory,
    )


if __name__ == "__main__":
    raise SystemExit(main())

