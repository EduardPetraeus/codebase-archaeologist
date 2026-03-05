"""Tests for PatternDetector analyzer."""

from __future__ import annotations

from codebase_archaeologist.analyzers.pattern_detector import PatternDetector


class TestPatternDetector:
    """Tests using the tmp_repo fixture from conftest."""

    def test_detects_snake_case_functions(self, tmp_repo):
        """Functions in tmp_repo are snake_case — detector should report high confidence."""
        detector = PatternDetector(repo_path=tmp_repo)
        result = detector.analyze()

        snake_conventions = [c for c in result.naming_conventions if c.pattern == "snake_case"]
        assert snake_conventions, "Expected a snake_case convention to be detected"
        assert snake_conventions[0].confidence > 0.80

    def test_detects_pascal_case_classes(self, tmp_repo):
        """Classes in tmp_repo (User) are PascalCase."""
        detector = PatternDetector(repo_path=tmp_repo)
        result = detector.analyze()

        pascal_conventions = [c for c in result.naming_conventions if c.pattern == "PascalCase"]
        assert pascal_conventions, "Expected a PascalCase convention to be detected"
        assert pascal_conventions[0].confidence > 0.80

    def test_detects_src_layout_pattern(self, tmp_repo):
        """tmp_repo has a src/ directory."""
        detector = PatternDetector(repo_path=tmp_repo)
        result = detector.analyze()

        assert "src-layout" in result.architecture_patterns

    def test_detects_pytest(self, tmp_repo):
        """Test files in tmp_repo define test_ functions, implying pytest."""
        detector = PatternDetector(repo_path=tmp_repo)
        result = detector.analyze()

        assert "pytest" in result.test_patterns

    def test_calculates_type_hint_ratio(self, tmp_repo):
        """utils.py has type hints — ratio should be > 0."""
        detector = PatternDetector(repo_path=tmp_repo)
        result = detector.analyze()

        assert result.type_hint_ratio > 0

    def test_calculates_docstring_ratio(self, tmp_repo):
        """Several functions in tmp_repo have docstrings."""
        detector = PatternDetector(repo_path=tmp_repo)
        result = detector.analyze()

        assert result.docstring_ratio > 0

    def test_empty_repo(self, tmp_path):
        """An empty directory should return default PatternResult values."""
        empty = tmp_path / "empty-repo"
        empty.mkdir()

        detector = PatternDetector(repo_path=empty)
        result = detector.analyze()

        assert result.naming_conventions == []
        assert result.architecture_patterns == []
        assert result.test_patterns == []
        assert result.type_hint_ratio == 0.0
        assert result.docstring_ratio == 0.0
        assert result.avg_function_length == 0.0
        assert result.has_type_checking is False

    def test_non_python_files_skipped(self, tmp_path):
        """A directory with only .txt files should return defaults."""
        text_dir = tmp_path / "text-only"
        text_dir.mkdir()
        (text_dir / "notes.txt").write_text("Just some notes.")
        (text_dir / "readme.txt").write_text("Read me.")

        detector = PatternDetector(repo_path=text_dir)
        result = detector.analyze()

        assert result.naming_conventions == []
        assert result.architecture_patterns == []
        assert result.test_patterns == []
        assert result.type_hint_ratio == 0.0
        assert result.docstring_ratio == 0.0
