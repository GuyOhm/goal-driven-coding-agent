"""Utilities to discover Polyglot Benchmark exercises."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class BenchmarkDiscoveryError(RuntimeError):
    """Raised when benchmark exercises cannot be located or parsed."""


@dataclass(slots=True)
class BenchmarkExercise:
    """Represents a single Polyglot Benchmark exercise on disk."""

    slug: str
    workspace_root: Path
    root: Path
    solution_file: Path
    test_file: Path
    instructions_markdown: str

    @property
    def display_name(self) -> str:
        """Return a human readable name derived from the slug."""
        return self.slug.replace("-", " ").title()

    @property
    def relative_directory(self) -> str:
        """Return the exercise directory relative to the workspace root."""
        return self._relative_path(self.root)

    @property
    def relative_solution_file(self) -> str:
        """Return the solution file path relative to the workspace root."""
        return self._relative_path(self.solution_file)

    @property
    def relative_test_file(self) -> str:
        """Return the test file path relative to the workspace root."""
        return self._relative_path(self.test_file)

    def build_goal(self) -> str:
        """Compose the goal text that will be handed to the coding agent."""
        instructions = self.instructions_markdown.strip()
        return (
            f"Primary goal: implement `{self.relative_solution_file}` so the canonical test suite "
            f"`pytest {self.relative_test_file}` passes.\n"
            f"- Run this command from the repository root (sandbox root): `pytest {self.relative_test_file}`.\n"
            f"- If you `cd` into `{self.relative_directory}`, run `pytest {self.test_file.name}` instead.\n"
            "Workflow checklist:\n"
            "1. Inspect the current solution file.\n"
            "2. Plan the necessary changes.\n"
            "3. Edit the solution.\n"
            "4. Run the pytest command above.\n"
            "5. Repeat until pytest is green.\n"
            "Rules:\n"
            "- Do not create or edit alternate test files; always rely on the provided pytest module.\n"
            "- Only modify files inside this exercise directory unless explicitly instructed.\n"
            "- If pytest reports 'collected 0 items', inspect the file structure/imports instead of "
            "rewriting tests.\n\n"
            f"Exercise instructions (verbatim from upstream docs):\n{instructions}"
        )

    def _relative_path(self, path: Path) -> str:
        return path.relative_to(self.workspace_root).as_posix()

    def build_context_blocks(self) -> list[str]:
        """Return structured context snippets for LLM prompts."""
        blocks: list[str] = []
        instructions = self.instructions_markdown.strip()
        if instructions:
            blocks.append(
                f"Exercise instructions ({self.relative_directory}/.docs):\n{instructions}"
            )
        blocks.extend(
            snippet
            for snippet in (
                self._render_file_block(self.solution_file),
                self._render_file_block(self.test_file),
            )
            if snippet
        )
        return blocks

    def _render_file_block(self, path: Path) -> str | None:
        if not path.exists():
            return None
        try:
            contents = path.read_text(encoding="utf-8").rstrip()
        except OSError as exc:
            return f"Unable to read `{self._relative_path(path)}` ({exc})."
        if not contents:
            return None
        return f"File `{self._relative_path(path)}`:\n{contents}"


class BenchmarkSuiteLoader:
    """Loads the list of benchmark exercises for the CLI."""

    def __init__(self, sandbox_root: Path):
        self._workspace_root = Path(sandbox_root).resolve()
        self._practice_root = (
            self._workspace_root / "benchmarks" / "python" / "exercises" / "practice"
        )

    @property
    def practice_root(self) -> Path:
        """Return the root directory that contains practice exercises."""
        return self._practice_root

    def discover(self, *, limit: int | None = None) -> list[BenchmarkExercise]:
        """Discover benchmark exercises up to the provided limit."""
        self._validate_limit(limit)
        if not self._practice_root.exists():
            raise BenchmarkDiscoveryError(
                f"Benchmark directory {self._practice_root} does not exist."
            )
        directories = sorted(
            (entry for entry in self._practice_root.iterdir() if entry.is_dir()),
            key=lambda directory: directory.name,
        )
        exercises: list[BenchmarkExercise] = []
        for directory in directories:
            exercises.append(self._build_exercise(directory))
            if limit is not None and len(exercises) >= limit:
                break
        return exercises

    def _build_exercise(self, directory: Path) -> BenchmarkExercise:
        slug = directory.name
        instructions = self._read_instructions(directory / ".docs")
        stem = slug.replace("-", "_")
        solution_file = directory / f"{stem}.py"
        test_file = directory / f"{stem}_test.py"
        if not solution_file.exists():
            raise BenchmarkDiscoveryError(
                f"Expected solution file {solution_file} to exist for {slug}."
            )
        if not test_file.exists():
            raise BenchmarkDiscoveryError(
                f"Expected test file {test_file} to exist for {slug}."
            )
        return BenchmarkExercise(
            slug=slug,
            workspace_root=self._workspace_root,
            root=directory,
            solution_file=solution_file,
            test_file=test_file,
            instructions_markdown=instructions,
        )

    def _read_instructions(self, docs_dir: Path) -> str:
        if not docs_dir.exists():
            raise BenchmarkDiscoveryError(
                f"Documentation directory {docs_dir} is missing."
            )
        markdown_files = sorted(
            (path for path in docs_dir.iterdir() if path.suffix == ".md"),
            key=lambda path: path.name,
        )
        if not markdown_files:
            raise BenchmarkDiscoveryError(
                f"No markdown instructions found in {docs_dir}."
            )
        contents: list[str] = []
        for file_path in markdown_files:
            text = file_path.read_text(encoding="utf-8").strip()
            if text:
                contents.append(text)
        if not contents:
            raise BenchmarkDiscoveryError(
                f"Markdown files in {docs_dir} are empty."
            )
        return "\n\n".join(contents)

    @staticmethod
    def _validate_limit(limit: int | None) -> None:
        if limit is None:
            return
        if limit <= 0:
            raise ValueError("--benchmarks-limit must be a positive integer.")

