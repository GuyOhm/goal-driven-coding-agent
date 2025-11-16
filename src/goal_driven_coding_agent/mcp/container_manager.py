"""Utility for orchestrating MCP docker-compose stacks per agent run."""

from __future__ import annotations

import logging
import socket
import subprocess
import time
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _parse_host_port(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported MCP server URL scheme: {parsed.scheme}")
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


def _wait_for_ports(endpoints: Sequence[tuple[str, int]], timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    pending = list(endpoints)
    while pending and time.time() < deadline:
        ready: list[tuple[str, int]] = []
        for host, port in pending:
            try:
                with socket.create_connection((host, port), timeout=1):
                    ready.append((host, port))
            except OSError:
                continue
        pending = [ep for ep in pending if ep not in ready]
        if pending:
            time.sleep(0.5)
    if pending:
        raise RuntimeError(f"MCP endpoints failed to become ready: {pending}")


@dataclass(slots=True)
class McpContainerManager(AbstractContextManager["McpContainerManager"]):
    """Start and stop MCP docker-compose services for the agent."""

    compose_file: Path
    project_name: str
    server_urls: Sequence[str]
    run_id: str
    _running: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.compose_file = self.compose_file.resolve()
        if not self.compose_file.exists():
            raise FileNotFoundError(f"MCP compose file not found: {self.compose_file}")

    def __enter__(self) -> "McpContainerManager":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._running:
            return
        command = [
            "docker",
            "compose",
            "-f",
            str(self.compose_file),
            "-p",
            self.project_name,
            "up",
            "-d",
            "--build",
            "--remove-orphans",
        ]
        logger.info("Starting MCP docker stack via %s", " ".join(command))
        env = os.environ.copy()
        env.setdefault("SANDBOX_ROOT", f"/sandbox/{self.run_id}")
        try:
            subprocess.run(command, check=True, env=env)
        except FileNotFoundError as exc:  # pragma: no cover - environment specific
            raise RuntimeError(
                "Docker is required to start MCP servers automatically, "
                "but the `docker` executable was not found."
            ) from exc
        _wait_for_ports([_parse_host_port(url) for url in self.server_urls])
        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        command = [
            "docker",
            "compose",
            "-f",
            str(self.compose_file),
            "-p",
            self.project_name,
            "down",
            "--remove-orphans",
        ]
        logger.info("Stopping MCP docker stack via %s", " ".join(command))
        env = os.environ.copy()
        env.setdefault("SANDBOX_ROOT", f"/sandbox/{self.run_id}")
        try:
            subprocess.run(command, check=False, env=env)
        finally:
            self._running = False

