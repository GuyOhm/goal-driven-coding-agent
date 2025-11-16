"""Convenience entry point for running the goal-driven coding agent CLI."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from goal_driven_coding_agent.cli.main import main as cli_main


def main() -> int:
    """Invoke the CLI runner."""
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
