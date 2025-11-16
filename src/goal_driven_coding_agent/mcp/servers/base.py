"""Shared utilities for MCP server implementations."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

DEFAULT_SANDBOX_ROOT = "/sandbox"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_TRANSPORT: Literal["stdio", "sse", "streamable-http"] = "stdio"


@dataclass(slots=True)
class BaseServerConfig:
    """Configuration shared by all MCP servers."""

    sandbox_root: Path
    transport: Literal["stdio", "sse", "streamable-http"]
    host: str
    port: int
    mount_path: str
    log_level: str


def resolve_sandbox_root(path: str | None) -> Path:
    """Resolve and create the sandbox path."""
    sandbox_root = Path(path or DEFAULT_SANDBOX_ROOT).resolve()
    sandbox_root.mkdir(parents=True, exist_ok=True)
    return sandbox_root


def read_env_var(name: str, default: str | None = None) -> str | None:
    """Fetch an environment variable, respecting empty values."""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def within_sandbox(root: Path, relative_path: str) -> Path:
    """Return a sandbox path ensuring no traversal outside root."""
    target = (root / (relative_path or ".")).resolve()
    root_resolved = root.resolve()
    if not str(target).startswith(str(root_resolved)):
        raise ValueError("Access outside of the sandbox root is not permitted.")
    return target


def build_base_config_from_env(prefix: str = "") -> BaseServerConfig:
    """Construct a base server configuration from environment variables."""
    def env(key: str, default: str | None = None) -> str | None:
        return read_env_var(f"{prefix}{key}", default)

    sandbox_root = resolve_sandbox_root(env("SANDBOX_ROOT"))
    transport_value = (env("TRANSPORT", DEFAULT_TRANSPORT) or DEFAULT_TRANSPORT).lower()
    if transport_value not in {"stdio", "sse", "streamable-http"}:
        raise ValueError(f"Unsupported MCP transport: {transport_value}")
    transport = cast(Literal["stdio", "sse", "streamable-http"], transport_value)

    host = env("HOST", "0.0.0.0") or "0.0.0.0"
    port = int(env("PORT", "8000") or "8000")
    mount_path = env("MOUNT_PATH", "/") or "/"
    log_level = env("LOG_LEVEL", DEFAULT_LOG_LEVEL) or DEFAULT_LOG_LEVEL
    return BaseServerConfig(
        sandbox_root=sandbox_root,
        transport=transport,  # type: ignore[arg-type]
        host=host,
        port=port,
        mount_path=mount_path,
        log_level=log_level.upper(),
    )

