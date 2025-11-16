"""Mock MCP tooling used for early agent development."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

from agents.tool import FunctionTool, Tool
from agents.tool_context import ToolContext

logger = logging.getLogger(__name__)


def _safe_json_load(arguments: str | None) -> dict[str, Any]:
    """Best-effort JSON parsing for tool arguments."""
    if not arguments:
        return {}
    try:
        return json.loads(arguments)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload supplied to tool: {exc}") from exc


def _normalize_relative_path(base: Path, relative_path: str) -> Path:
    """Resolve and validate sandbox paths."""
    relative_path = relative_path or "."
    resolved = (base / relative_path).resolve()
    if not str(resolved).startswith(str(base.resolve())):
        raise ValueError("Access outside of the sandbox root is not permitted.")
    return resolved


@dataclass(slots=True)
class MockSandboxFilesystem:
    """Mock filesystem exposed via MCP function tools."""

    sandbox_root: Path

    def __post_init__(self) -> None:
        self.sandbox_root.mkdir(parents=True, exist_ok=True)

    async def list_directory(self, context: ToolContext[Any], arguments: str) -> dict[str, Any]:
        payload = _safe_json_load(arguments)
        relative_path = payload.get("path", ".")
        target = _normalize_relative_path(self.sandbox_root, relative_path)
        entries: list[dict[str, Any]] = []
        if target.exists():
            for item in sorted(target.iterdir()):
                entries.append(
                    {
                        "name": item.name,
                        "is_dir": item.is_dir(),
                        "size_bytes": item.stat().st_size,
                    }
                )
        logger.debug("Listed %s entries under %s", len(entries), target)
        return {"path": str(relative_path), "entries": entries}

    async def read_text(self, context: ToolContext[Any], arguments: str) -> dict[str, Any]:
        payload = _safe_json_load(arguments)
        relative_path = payload.get("path")
        if not relative_path:
            raise ValueError("`path` is required for sandbox_read_file.")
        target = _normalize_relative_path(self.sandbox_root, relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File {relative_path} not found.")
        content = target.read_text(encoding="utf-8")
        logger.debug("Read file %s (%d bytes)", target, len(content))
        return {"path": relative_path, "content": content}

    async def write_text(self, context: ToolContext[Any], arguments: str) -> dict[str, Any]:
        payload = _safe_json_load(arguments)
        relative_path = payload.get("path")
        content = payload.get("content", "")
        if not relative_path:
            raise ValueError("`path` is required for sandbox_write_file.")
        target = _normalize_relative_path(self.sandbox_root, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.debug(
            "Wrote %d bytes to %s for run %s",
            len(content),
            target,
            context.context.run_id if hasattr(context.context, "run_id") else "unknown",
        )
        return {"path": relative_path, "bytes_written": len(content)}


@dataclass(slots=True)
class MockSandboxExecutor:
    """Mock executor that emulates code execution inside the sandbox."""

    execution_log: list[dict[str, Any]] = field(default_factory=list)

    async def run_python(self, context: ToolContext[Any], arguments: str) -> dict[str, Any]:
        payload = _safe_json_load(arguments)
        code = payload.get("code", "")
        file_path = payload.get("file_path")
        execution_id = uuid.uuid4().hex[:8]
        result = {
            "execution_id": execution_id,
            "stdout": (
                "Mock execution succeeded. (Replace with Docker-backed executor.)"
            ),
            "stderr": "",
            "exit_code": 0,
            "summary": f"Executed {'inline code' if code else file_path or 'unknown source'}",
        }
        loop = asyncio.get_running_loop()
        self.execution_log.append(
            {
                "execution_id": execution_id,
                "code": code,
                "file_path": file_path,
                "timestamp": loop.time(),
            }
        )
        logger.debug("Mock executor recorded run %s", execution_id)
        return result


@dataclass(slots=True)
class MockMcpToolset:
    """Aggregates the mock filesystem and executor into tool declarations."""

    filesystem: MockSandboxFilesystem
    executor: MockSandboxExecutor
    tools: list[Tool] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.tools = create_mock_mcp_tools(self.filesystem, self.executor)

    def describe_tools(self) -> str:
        """Return a human-readable representation of the available tools."""
        return "\n".join(f"- {tool.name}: {tool.description}" for tool in self.tools)


def _function_tool(
    *,
    name: str,
    description: str,
    schema: dict[str, Any],
    handler: Callable[[ToolContext[Any], str], Any],
) -> FunctionTool:
    return FunctionTool(
        name=name,
        description=description,
        params_json_schema=schema,
        on_invoke_tool=handler,
    )


def create_mock_mcp_tools(
    filesystem: MockSandboxFilesystem,
    executor: MockSandboxExecutor,
) -> list[Tool]:
    """Create all mock MCP tools used by the coding agent."""
    tools: list[Tool] = [
        _function_tool(
            name="sandbox_list_directory",
            description="List files and directories inside the sandbox volume.",
            schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path under the sandbox root.",
                        "default": ".",
                    }
                },
            },
            handler=filesystem.list_directory,
        ),
        _function_tool(
            name="sandbox_read_file",
            description="Read a UTF-8 text file from the sandbox.",
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path."}
                },
                "required": ["path"],
            },
            handler=filesystem.read_text,
        ),
        _function_tool(
            name="sandbox_write_file",
            description="Write UTF-8 text content to a file in the sandbox.",
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path."},
                    "content": {
                        "type": "string",
                        "description": "Full file contents to be written.",
                    },
                },
                "required": ["path", "content"],
            },
            handler=filesystem.write_text,
        ),
        _function_tool(
            name="sandbox_run_python",
            description="Execute Python code inside the sandbox (mock executor).",
            schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Inline Python snippet to execute.",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Optional path to an existing python file to run.",
                    },
                },
            },
            handler=executor.run_python,
        ),
    ]
    return tools

