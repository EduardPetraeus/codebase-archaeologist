"""Analyzer for codebase structure: languages, layout, entry points, CI, and config."""

from __future__ import annotations

from pathlib import Path

from codebase_archaeologist.analyzers.base import BaseAnalyzer
from codebase_archaeologist.models import CodeStructureResult, ConfigFile, EntryPoint

# Extension → language mapping
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".cs": "C#",
}

# Known CI system indicators
CI_INDICATORS: dict[str, str] = {
    ".github/workflows": "GitHub Actions",
    ".gitlab-ci.yml": "GitLab CI",
    "Jenkinsfile": "Jenkins",
    ".circleci": "CircleCI",
    ".travis.yml": "Travis CI",
}

# Config files to detect
CONFIG_FILE_NAMES: set[str] = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
}

# Entry point file names and their types
ENTRY_POINT_FILES: dict[str, str] = {
    "main.py": "main",
    "app.py": "server",
    "server.py": "server",
    "cli.py": "cli",
    "manage.py": "cli",
    "__main__.py": "main",
    "index.js": "main",
    "index.ts": "main",
}

# Maximum number of files to sample for line counting
LINE_COUNT_SAMPLE_SIZE = 200


class CodeStructureAnalyzer(BaseAnalyzer):
    """Analyzes codebase structure: languages, layout, entry points, CI, and config."""

    def analyze(self) -> CodeStructureResult:
        """Run full code structure analysis."""
        result = CodeStructureResult()

        all_files = self._collect_files()
        result.total_files = len(all_files)

        # Language detection
        language_counts = self._count_languages(all_files)
        result.languages = language_counts
        if language_counts:
            result.primary_language = max(language_counts, key=language_counts.get)

        # Line counting (sampled)
        result.total_lines = self._count_lines(all_files)

        # Layout detection
        result.src_layout = self._detect_src_layout()
        result.has_tests, result.test_directory = self._detect_tests()

        # CI detection
        result.has_ci, result.ci_system = self._detect_ci()

        # Config files
        result.config_files = self._detect_config_files()

        # Entry points
        result.entry_points = self._detect_entry_points(all_files)

        # Directory tree (top 2 levels)
        result.directory_tree = self._build_directory_tree()

        return result

    def _count_languages(self, files: list[Path]) -> dict[str, int]:
        """Count files per detected language."""
        counts: dict[str, int] = {}
        for f in files:
            lang = EXTENSION_LANGUAGE_MAP.get(f.suffix)
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
        return counts

    def _count_lines(self, files: list[Path]) -> int:
        """Count total lines across a sample of files."""
        code_extensions = set(EXTENSION_LANGUAGE_MAP.keys())
        code_files = [f for f in files if f.suffix in code_extensions]
        sampled = code_files[:LINE_COUNT_SAMPLE_SIZE]

        total = 0
        for f in sampled:
            content = self._safe_read(f)
            if content is not None:
                total += len(content.splitlines())
        return total

    def _detect_src_layout(self) -> bool:
        """Check if the repo uses a src/ directory layout with code inside."""
        src_dir = self.repo_path / "src"
        if not src_dir.is_dir():
            return False
        # Check that src/ contains at least one code file
        code_extensions = set(EXTENSION_LANGUAGE_MAP.keys())
        for f in src_dir.rglob("*"):
            if f.is_file() and f.suffix in code_extensions:
                return True
        return False

    def _detect_tests(self) -> tuple[bool, str]:
        """Look for test directories."""
        for test_dir_name in ("tests", "test", "spec"):
            candidate = self.repo_path / test_dir_name
            if candidate.is_dir():
                return True, f"{test_dir_name}/"
        return False, ""

    def _detect_ci(self) -> tuple[bool, str]:
        """Detect CI/CD system."""
        for indicator, system in CI_INDICATORS.items():
            path = self.repo_path / indicator
            if path.exists():
                return True, system
        return False, ""

    def _detect_config_files(self) -> list[ConfigFile]:
        """Find known configuration files at the repo root."""
        found: list[ConfigFile] = []
        for name in sorted(CONFIG_FILE_NAMES):
            path = self.repo_path / name
            if path.is_file():
                found.append(ConfigFile(path=name, type=name))
        return found

    def _detect_entry_points(self, all_files: list[Path]) -> list[EntryPoint]:
        """Find entry point files and pyproject.toml script definitions."""
        entry_points: list[EntryPoint] = []
        seen_paths: set[str] = set()

        # File-based entry points
        for f in all_files:
            if f.name in ENTRY_POINT_FILES:
                rel = str(f.relative_to(self.repo_path))
                if rel not in seen_paths:
                    seen_paths.add(rel)
                    entry_points.append(
                        EntryPoint(
                            path=rel,
                            type=ENTRY_POINT_FILES[f.name],
                            description=f"Detected from filename: {f.name}",
                        )
                    )

        # pyproject.toml [project.scripts] entry points
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.is_file():
            self._extract_pyproject_scripts(pyproject, entry_points, seen_paths)

        return entry_points

    def _extract_pyproject_scripts(
        self,
        pyproject: Path,
        entry_points: list[EntryPoint],
        seen_paths: set[str],
    ) -> None:
        """Parse pyproject.toml for [project.scripts] entry points."""
        try:
            content = pyproject.read_text(encoding="utf-8")
        except OSError:
            return

        # Use a simple TOML parser approach — look for [project.scripts] section
        # We avoid heavy dependencies by parsing manually
        in_scripts_section = False
        for line in content.splitlines():
            stripped = line.strip()

            if stripped == "[project.scripts]":
                in_scripts_section = True
                continue

            if in_scripts_section:
                if stripped.startswith("["):
                    # New section, stop
                    break
                if "=" in stripped and not stripped.startswith("#"):
                    name, _, target = stripped.partition("=")
                    name = name.strip().strip('"').strip("'")
                    target = target.strip().strip('"').strip("'")
                    key = f"pyproject.toml:scripts:{name}"
                    if key not in seen_paths:
                        seen_paths.add(key)
                        entry_points.append(
                            EntryPoint(
                                path=target,
                                type="cli",
                                description=f"Script '{name}' defined in pyproject.toml",
                            )
                        )

    def _build_directory_tree(self) -> dict[str, list[str]]:
        """Build a directory tree representation (top 2 levels), respecting .gitignore."""
        tree: dict[str, list[str]] = {}

        # Level 0: repo root
        root_entries: list[str] = []
        for item in sorted(self.repo_path.iterdir()):
            if self._is_path_gitignored(item):
                continue
            root_entries.append(item.name + ("/" if item.is_dir() else ""))
        tree["."] = root_entries

        # Level 1: immediate subdirectories
        for item in sorted(self.repo_path.iterdir()):
            if not item.is_dir() or item.name.startswith("."):
                continue
            if self._is_path_gitignored(item):
                continue
            sub_entries: list[str] = []
            try:
                for child in sorted(item.iterdir()):
                    if self._is_path_gitignored(child):
                        continue
                    sub_entries.append(child.name + ("/" if child.is_dir() else ""))
            except PermissionError:
                continue
            tree[item.name] = sub_entries

        return tree
