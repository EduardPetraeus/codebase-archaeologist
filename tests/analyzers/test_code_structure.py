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
