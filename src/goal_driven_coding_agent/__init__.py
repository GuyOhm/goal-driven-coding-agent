"""Top-level package for the goal-driven coding agent project."""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - metadata lookup
    __version__ = version("goal-driven-coding-agent")
except PackageNotFoundError:  # pragma: no cover - local dev
    __version__ = "0.0.0"

__all__ = ["__version__"]

