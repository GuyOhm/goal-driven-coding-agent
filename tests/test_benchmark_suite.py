"""Tests for Polyglot Benchmark discovery utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from goal_driven_coding_agent.benchmarks import (
    BenchmarkDiscoveryError,
    BenchmarkSuiteLoader,
)


def _create_exercise(tmp_path: Path, slug: str, instructions: str = "Solve it.") -> None:
    exercise_root = (
        tmp_path / "benchmarks" / "python" / "exercises" / "practice" / slug
    )
    docs_dir = exercise_root / ".docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "instructions.md").write_text(instructions, encoding="utf-8")
    snake = slug.replace("-", "_")
    (exercise_root / f"{snake}.py").write_text("# solution", encoding="utf-8")
    (exercise_root / f"{snake}_test.py").write_text("# tests", encoding="utf-8")


def test_discover_builds_goal_from_markdown(tmp_path: Path) -> None:
    _create_exercise(tmp_path, "affine-cipher", "Implement the affine cipher.")
    loader = BenchmarkSuiteLoader(tmp_path)

    exercises = loader.discover()

    assert len(exercises) == 1
    goal_text = exercises[0].build_goal()
    assert "Implement the affine cipher." in goal_text
    assert "affine_cipher_test.py" in goal_text


def test_discover_applies_limit(tmp_path: Path) -> None:
    _create_exercise(tmp_path, "affine-cipher")
    _create_exercise(tmp_path, "beer-song")
    loader = BenchmarkSuiteLoader(tmp_path)

    limited = loader.discover(limit=1)

    assert len(limited) == 1
    assert limited[0].slug == "affine-cipher"


def test_missing_docs_raise_error(tmp_path: Path) -> None:
    slug = "affine-cipher"
    exercise_root = (
        tmp_path / "benchmarks" / "python" / "exercises" / "practice" / slug
    )
    exercise_root.mkdir(parents=True, exist_ok=True)
    snake = slug.replace("-", "_")
    (exercise_root / f"{snake}.py").write_text("# solution", encoding="utf-8")
    (exercise_root / f"{snake}_test.py").write_text("# tests", encoding="utf-8")
    loader = BenchmarkSuiteLoader(tmp_path)

    with pytest.raises(BenchmarkDiscoveryError):
        loader.discover()


def test_build_context_blocks_includes_instructions_and_files(tmp_path: Path) -> None:
    instructions = "Specific instructions."
    _create_exercise(tmp_path, "affine-cipher", instructions)
    loader = BenchmarkSuiteLoader(tmp_path)
    exercise = loader.discover()[0]

    blocks = exercise.build_context_blocks()

    assert any("Specific instructions." in block for block in blocks)
    assert any("affine_cipher.py" in block for block in blocks)
    assert any("affine_cipher_test.py" in block for block in blocks)


