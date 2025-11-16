"""Code execution MCP server backed by a sandboxed Docker container."""

from __future__ import annotations

import argparse
import logging
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence, cast

from mcp.server.fastmcp import FastMCP

from goal_driven_coding_agent.mcp.servers.base import (
    BaseServerConfig,
    build_base_config_from_env,
    read_env_var,
    within_sandbox,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExecutorServerConfig(BaseServerConfig):
    """Configuration for the executor MCP server."""

    python_binary: str = "python"
    default_timeout_seconds: int = 300


def create_executor_server(config: ExecutorServerConfig) -> FastMCP:
    """Instantiate the executor MCP server."""
    server = FastMCP(
        name="SandboxExecutor",
        instructions="Executes code within the sandbox with strict isolation.",
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )
    sandbox_root = config.sandbox_root

    def _run_subprocess(
        command: Sequence[str],
        *,
        cwd: Path,
        timeout: int,
    ) -> dict[str, Any]:
        start_time = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.perf_counter() - start_time
            return {
                "command": command,
                "cwd": str(cwd),
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "duration_seconds": duration,
            }
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start_time
            return {
                "command": command,
                "cwd": str(cwd),
                "exit_code": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "duration_seconds": duration,
                "timeout": True,
            }

    @server.tool(name="sandbox_run_command", description="Execute a shell command inside the sandbox.")
    async def run_command(command: str, workdir: str = ".", timeout_seconds: int | None = None) -> dict[str, Any]:
        cwd = within_sandbox(sandbox_root, workdir)
        timeout = timeout_seconds or config.default_timeout_seconds
        command_args = ["bash", "-lc", command]
        return _run_subprocess(command_args, cwd=cwd, timeout=timeout)

    @server.tool(name="sandbox_run_python_file", description="Execute a Python script from the sandbox.")
    async def run_python_file(path: str, args: str | None = None, timeout_seconds: int | None = None) -> dict[str, Any]:
        target = within_sandbox(sandbox_root, path)
        if not target.exists():
            raise FileNotFoundError(f"Python file not found: {path}")
        timeout = timeout_seconds or config.default_timeout_seconds
        arg_list = shlex.split(args) if args else []
        command = [config.python_binary, str(target), *arg_list]
        return _run_subprocess(command, cwd=target.parent, timeout=timeout)

    @server.tool(name="sandbox_run_python_snippet", description="Run inline Python code as a temporary script.")
    async def run_python_snippet(code: str, timeout_seconds: int | None = None) -> dict[str, Any]:
        if not code.strip():
            raise ValueError("Code snippet must not be empty.")
        tmp_file = sandbox_root / "_tmp_snippet.py"
        tmp_file.write_text(code, encoding="utf-8")
        timeout = timeout_seconds or config.default_timeout_seconds
        command = [config.python_binary, str(tmp_file)]
        result = _run_subprocess(command, cwd=sandbox_root, timeout=timeout)
        tmp_file.unlink(missing_ok=True)
        return result

    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the sandbox executor MCP server.")
    parser.add_argument("--transport", default=None, help="MCP transport (stdio, sse, streamable-http).")
    parser.add_argument("--host", default=None, help="Server host for SSE/HTTP transports.")
    parser.add_argument("--port", default=None, help="Server port for SSE/HTTP transports.")
    parser.add_argument("--mount-path", default=None, help="Mount path used for SSE transports.")
    parser.add_argument("--log-level", default=None, help="Logging level.")
    parser.add_argument("--sandbox-root", default=None, help="Sandbox root directory.")
    parser.add_argument("--python-binary", default=None, help="Python executable used for scripts.")
    parser.add_argument("--timeout-seconds", default=None, type=int, help="Default execution timeout.")
    return parser.parse_args()


def _merge_config(args: argparse.Namespace) -> ExecutorServerConfig:
    base = build_base_config_from_env(prefix="")
    sandbox_root = Path(args.sandbox_root or str(base.sandbox_root)).resolve()
    sandbox_root.mkdir(parents=True, exist_ok=True)
    transport_value = (args.transport or base.transport).lower()
    if transport_value not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(f"Unsupported transport: {transport_value}")
    transport = cast(Literal["stdio", "sse", "streamable-http"], transport_value)
    python_binary = args.python_binary or read_env_var("PYTHON_BINARY") or "python"
    timeout_value = args.timeout_seconds or int(read_env_var("TIMEOUT_SECONDS", "300") or "300")
    return ExecutorServerConfig(
        sandbox_root=sandbox_root,
        transport=transport,
        host=args.host or base.host,
        port=int(args.port or base.port),
        mount_path=args.mount_path or base.mount_path,
        log_level=(args.log_level or base.log_level).upper(),
        python_binary=python_binary,
        default_timeout_seconds=timeout_value,
    )


def run_executor_server(config: ExecutorServerConfig) -> None:
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    server = create_executor_server(config)
    server.run(transport=config.transport, mount_path=config.mount_path)


def main() -> None:
    args = parse_args()
    config = _merge_config(args)
    run_executor_server(config)


if __name__ == "__main__":
    main()

