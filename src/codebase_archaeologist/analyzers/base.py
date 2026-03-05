"""Base class for all analyzers."""

from abc import ABC, abstractmethod
from pathlib import Path

MAX_FILE_SIZE = 1_000_000  # 1 MB — skip files larger than this


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
        resolved_root = self.repo_path.resolve()
        files = []
        for f in self.repo_path.rglob("*"):
            if f.is_symlink():
                continue
            if not f.is_file():
                continue
            # Verify file is within repo (prevent symlink escapes)
            try:
                f.resolve().relative_to(resolved_root)
            except ValueError:
                continue
            if any(d in f.parts for d in exclude_dirs):
                continue
            if extensions is not None and f.suffix not in extensions:
                continue
            files.append(f)
            if len(files) >= self.max_files:
                break
        return files

    @staticmethod
    def _safe_read(filepath: Path) -> str | None:
        """Read file content safely, skipping oversized or binary files."""
        try:
            if filepath.stat().st_size > MAX_FILE_SIZE:
                return None
            return filepath.read_text(errors="ignore")
        except (OSError, UnicodeDecodeError):
            return None
