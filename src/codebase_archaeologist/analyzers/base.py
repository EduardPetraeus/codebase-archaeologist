"""Base class for all analyzers."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseAnalyzer(ABC):
    """Abstract base for codebase analyzers."""

    def __init__(self, repo_path: Path, max_files: int = 500):
        self.repo_path = repo_path
        self.max_files = max_files

    @abstractmethod
    def analyze(self):
        """Run analysis and return a result dataclass."""

    def _collect_files(
        self, extensions: set[str] | None = None, exclude_dirs: set[str] | None = None
    ) -> list[Path]:
        """Collect files from repo, respecting max_files limit."""
        if exclude_dirs is None:
            exclude_dirs = {
                ".git",
                "__pycache__",
                "node_modules",
                ".venv",
                "venv",
                ".tox",
                ".eggs",
                "dist",
                "build",
                ".mypy_cache",
                ".ruff_cache",
            }
        files = []
        for f in self.repo_path.rglob("*"):
            if f.is_file() and not any(d in f.parts for d in exclude_dirs):
                if extensions is None or f.suffix in extensions:
                    files.append(f)
            if len(files) >= self.max_files:
                break
        return files
