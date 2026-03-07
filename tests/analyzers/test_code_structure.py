"""Tests for CodeStructureAnalyzer."""

import subprocess
from pathlib import Path

from codebase_archaeologist.analyzers.code_structure import CodeStructureAnalyzer


class TestCodeStructureAnalyzer:
    """Test suite for code structure analysis."""

    def test_detects_python_as_primary_language(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        assert result.primary_language == "Python"

    def test_detects_src_layout(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        assert result.src_layout is True

    def test_detects_tests_directory(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        assert result.has_tests is True
        assert "tests" in result.test_directory

    def test_detects_ci(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        assert result.has_ci is True
        assert "GitHub Actions" in result.ci_system

    def test_finds_config_files(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        config_paths = [cf.path for cf in result.config_files]
        assert "pyproject.toml" in config_paths

    def test_finds_entry_points(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        entry_paths = [ep.path for ep in result.entry_points]
        assert any("main.py" in p for p in entry_paths)

    def test_counts_files_and_lines(self, tmp_repo: Path) -> None:
        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()
        assert result.total_files > 0
        assert result.total_lines > 0

    def test_empty_repo(self, tmp_path: Path) -> None:
        """An empty git repo should return safe defaults."""
        empty = tmp_path / "empty-repo"
        empty.mkdir()
        subprocess.run(["git", "init"], cwd=empty, capture_output=True, check=True)

        analyzer = CodeStructureAnalyzer(empty)
        result = analyzer.analyze()

        assert result.primary_language == "unknown"
        assert result.languages == {}
        assert result.total_files == 0
        assert result.total_lines == 0
        assert result.src_layout is False
        assert result.has_tests is False
        assert result.has_ci is False
        assert result.config_files == []
        assert result.entry_points == []

    def test_gitignored_files_excluded(self, tmp_repo: Path) -> None:
        """Files in gitignored directories should not appear in analysis."""
        # Create a venv-like directory with Python files
        venv = tmp_repo / ".venv-custom"
        venv.mkdir()
        pkg = venv / "lib" / "site-packages" / "somepkg"
        pkg.mkdir(parents=True)
        (pkg / "cli.py").write_text("def main():\n    pass\n")
        (pkg / "app.py").write_text("def run():\n    pass\n")

        # Add to .gitignore
        (tmp_repo / ".gitignore").write_text(".venv-custom/\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=tmp_repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore: add gitignore"],
            cwd=tmp_repo,
            capture_output=True,
            check=True,
        )

        analyzer = CodeStructureAnalyzer(tmp_repo)
        result = analyzer.analyze()

        # Entry points should NOT include files from .venv-custom
        entry_paths = [ep.path for ep in result.entry_points]
        for path in entry_paths:
            assert ".venv-custom" not in path, f"Gitignored file leaked: {path}"

        # Directory tree should NOT include .venv-custom
        root_items = result.directory_tree.get(".", [])
        assert ".venv-custom/" not in root_items

    def test_untracked_non_ignored_files_included(self, tmp_repo: Path) -> None:
        """New files not yet staged should still appear (they're not gitignored)."""
        # Create a new file without staging it
        (tmp_repo / "src" / "myproject" / "new_module.py").write_text(
            "def new_function():\n    pass\n"
        )

        analyzer = CodeStructureAnalyzer(tmp_repo)
        all_files = analyzer._collect_files(extensions={".py"})
        file_names = [f.name for f in all_files]
        assert "new_module.py" in file_names
