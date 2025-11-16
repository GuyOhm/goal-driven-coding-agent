"""Filesystem MCP server backed by a sandboxed Docker volume."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from mcp.server.fastmcp import FastMCP

from goal_driven_coding_agent.mcp.servers.base import (
    BaseServerConfig,
    build_base_config_from_env,
    within_sandbox,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FilesystemServerConfig(BaseServerConfig):
    """Configuration for the filesystem MCP server."""

    allow_binary: bool = False


def create_filesystem_server(config: FilesystemServerConfig) -> FastMCP:
    """Instantiate the filesystem MCP server."""
    server = FastMCP(
        name="SandboxFilesystem",
        instructions="Provides sandboxed filesystem access for the coding agent.",
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )

    sandbox_root = config.sandbox_root

    @server.tool(name="sandbox_list_directory", description="List entries within the sandbox.")
    async def list_directory(path: str = ".") -> dict[str, Any]:
        target = within_sandbox(sandbox_root, path)
        entries = []
        if target.exists():
            for entry in sorted(target.iterdir()):
                stat = entry.stat()
                entries.append(
                    {
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size_bytes": stat.st_size,
                        "modified_ts": stat.st_mtime,
                    }
                )
        return {"path": str(Path(path)), "entries": entries}

    @server.tool(name="sandbox_read_file", description="Read a UTF-8 encoded text file from the sandbox.")
    async def read_file(path: str) -> dict[str, Any]:
        target = within_sandbox(sandbox_root, path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = target.read_text(encoding="utf-8")
        return {"path": path, "content": content}

    @server.tool(name="sandbox_write_file", description="Write UTF-8 text content into a sandbox file.")
    async def write_file(path: str, content: str) -> dict[str, Any]:
        target = within_sandbox(sandbox_root, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"path": path, "bytes_written": len(content)}

    @server.tool(name="sandbox_make_directory", description="Create a directory (including parents) in the sandbox.")
    async def make_directory(path: str) -> dict[str, Any]:
        target = within_sandbox(sandbox_root, path)
        target.mkdir(parents=True, exist_ok=True)
        return {"path": path, "created": True}

    @server.tool(name="sandbox_remove_path", description="Delete a file or empty directory from the sandbox.")
    async def remove_path(path: str) -> dict[str, Any]:
        target = within_sandbox(sandbox_root, path)
        if target.is_dir():
            if any(target.iterdir()):
                raise ValueError("Cannot remove a non-empty directory.")
            target.rmdir()
        elif target.exists():
            target.unlink()
        else:
            raise FileNotFoundError(f"Path not found: {path}")
        return {"path": path, "removed": True}

    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the sandbox filesystem MCP server.")
    parser.add_argument("--transport", default=None, help="MCP transport (stdio, sse, streamable-http).")
    parser.add_argument("--host", default=None, help="Server host for SSE/HTTP transports.")
    parser.add_argument("--port", default=None, help="Server port for SSE/HTTP transports.")
    parser.add_argument("--mount-path", default=None, help="Mount path used for SSE transports.")
    parser.add_argument("--log-level", default=None, help="Logging level.")
    parser.add_argument("--sandbox-root", default=None, help="Sandbox root directory.")
    return parser.parse_args()


def _merge_config(args: argparse.Namespace) -> FilesystemServerConfig:
    base = build_base_config_from_env(prefix="")
    sandbox_root = Path(args.sandbox_root or str(base.sandbox_root)).resolve()
    sandbox_root.mkdir(parents=True, exist_ok=True)
    transport_value = (args.transport or base.transport).lower()
    if transport_value not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(f"Unsupported transport: {transport_value}")
    transport = cast(Literal["stdio", "sse", "streamable-http"], transport_value)
    merged = FilesystemServerConfig(
        sandbox_root=sandbox_root,
        transport=transport,
        host=args.host or base.host,
        port=int(args.port or base.port),
        mount_path=args.mount_path or base.mount_path,
        log_level=(args.log_level or base.log_level).upper(),
    )
    return merged


def run_filesystem_server(config: FilesystemServerConfig) -> None:
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    server = create_filesystem_server(config)
    server.run(transport=config.transport, mount_path=config.mount_path)


def main() -> None:
    args = parse_args()
    config = _merge_config(args)
    run_filesystem_server(config)


if __name__ == "__main__":
    main()

