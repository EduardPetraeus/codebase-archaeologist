"""Tests for GitHistoryAnalyzer."""

from pathlib import Path

from codebase_archaeologist.analyzers.git_history import GitHistoryAnalyzer


class TestGitHistoryAnalyzer:
    """Test suite for git history analysis."""

    def test_counts_commits(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        assert result.total_commits == 4

    def test_finds_contributors(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        assert len(result.contributors) == 2
        # "Test User" made 3 of 4 commits, should be first (sorted desc)
        assert result.contributors[0].name == "Test User"
        assert result.contributors[0].commit_count == 3

    def test_detects_hot_files(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        assert len(result.hot_files) > 0
        # Most changed files should be in the list
        hot_paths = [hf.path for hf in result.hot_files]
        assert any("main.py" in p or "utils.py" in p for p in hot_paths)

    def test_calculates_bus_factor(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        assert result.bus_factor >= 1

    def test_detects_conventional_commits(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        # All 4 commits use conventional format (feat, feat, feat, refactor)
        assert result.conventional_commits_ratio == 1.0

    def test_commit_dates(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        assert result.first_commit_date != ""
        assert result.last_commit_date != ""
        # Both should be ISO-format date strings
        assert len(result.first_commit_date) == 10  # YYYY-MM-DD
        assert len(result.last_commit_date) == 10

    def test_active_branches(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history)
        result = analyzer.analyze()
        assert len(result.active_branches) >= 1

    def test_not_a_git_repo(self, tmp_path: Path) -> None:
        """A plain directory (no git init) should return an empty result."""
        plain_dir = tmp_path / "not-a-repo"
        plain_dir.mkdir()

        analyzer = GitHistoryAnalyzer(plain_dir)
        result = analyzer.analyze()

        assert result.total_commits == 0
        assert result.contributors == []
        assert result.hot_files == []
        assert result.bus_factor == 0
        assert result.conventional_commits_ratio == 0.0
        assert result.active_branches == []

    def test_respects_max_commits(self, tmp_repo_with_history: Path) -> None:
        analyzer = GitHistoryAnalyzer(tmp_repo_with_history, max_commits=2)
        result = analyzer.analyze()
        assert result.total_commits == 2
