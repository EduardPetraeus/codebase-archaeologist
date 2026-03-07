"""Base class for all analyzers."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

MAX_FILE_SIZE = 1_000_000  # 1 MB — skip files larger than this

_FALLBACK_EXCLUDE_DIRS = frozenset(
    {
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
)


class BaseAnalyzer(ABC):
    """Abstract base for codebase analyzers."""

    def __init__(self, repo_path: Path, max_files: int = 500):
        self.repo_path = repo_path
        self.max_files = max_files
        self._git_files: set[Path] | None = None
        self._git_checked = False

    @abstractmethod
    def analyze(self):
        """Run analysis and return a result dataclass."""

    def _get_git_files(self) -> set[Path] | None:
        """Get the set of git-relevant files (tracked + untracked non-ignored).

        Returns None if the repo is not a git repo or git is unavailable.
        Result is cached for the lifetime of the analyzer instance.
        """
        if self._git_checked:
            return self._git_files
        self._git_checked = True
        try:
            result = subprocess.run(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                self._git_files = {
                    self.repo_path / line for line in result.stdout.strip().split("\n") if line
                }
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        return self._git_files

    def _is_path_gitignored(self, path: Path) -> bool:
        """Check if a path would be excluded by git.

        If git info is unavailable, falls back to hardcoded exclude dirs.
        """
        git_files = self._get_git_files()
        if git_files is not None:
            if path.is_file():
                return path not in git_files
            # For directories: check if any git file lives under this dir
            return not any(f.is_relative_to(path) for f in git_files)
        return any(d in path.parts for d in _FALLBACK_EXCLUDE_DIRS)

    def _collect_files(
        self,
        extensions: set[str] | None = None,
        exclude_dirs: set[str] | None = None,
    ) -> list[Path]:
        """Collect files from repo, respecting .gitignore and max_files limit."""
        resolved_root = self.repo_path.resolve()
        git_files = self._get_git_files()

        if git_files is not None:
            return self._collect_from_git(git_files, extensions, resolved_root)
        return self._collect_from_rglob(
            extensions, exclude_dirs or _FALLBACK_EXCLUDE_DIRS, resolved_root
        )

    def _collect_from_git(
        self,
        git_files: set[Path],
        extensions: set[str] | None,
        resolved_root: Path,
    ) -> list[Path]:
        """Collect files using git ls-files as the source of truth."""
        files = []
        for f in sorted(git_files):
            if f.is_symlink():
                continue
            if not f.is_file():
                continue
            try:
                f.resolve().relative_to(resolved_root)
            except ValueError:
                continue
            if extensions is not None and f.suffix not in extensions:
                continue
            files.append(f)
            if len(files) >= self.max_files:
                break
        return files

    def _collect_from_rglob(
        self,
        extensions: set[str] | None,
        exclude_dirs: frozenset[str] | set[str],
        resolved_root: Path,
    ) -> list[Path]:
        """Fallback: collect files via rglob with hardcoded exclude dirs."""
        files = []
        for f in self.repo_path.rglob("*"):
            if f.is_symlink():
                continue
            if not f.is_file():
                continue
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
