"""Analyzer for extracting git history: commits, contributors, hot files, bus factor."""

import re
from collections import defaultdict
from pathlib import Path

import git

from codebase_archaeologist.analyzers.base import BaseAnalyzer
from codebase_archaeologist.models import Contributor, GitHistoryResult, HotFile

CONVENTIONAL_COMMIT_PATTERN = re.compile(
    r"^(feat|fix|docs|refactor|test|chore|perf|ci|build|style)(\(.+\))?!?:"
)


class GitHistoryAnalyzer(BaseAnalyzer):
    """Extract institutional knowledge from git history."""

    def __init__(self, repo_path: Path, max_files: int = 500, max_commits: int = 1000):
        super().__init__(repo_path, max_files)
        self.max_commits = max_commits

    def analyze(self) -> GitHistoryResult:
        """Analyze git history and return structured results."""
        try:
            repo = git.Repo(self.repo_path)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return GitHistoryResult()

        # Collect commits
        try:
            commits = list(repo.iter_commits(max_count=self.max_commits))
        except ValueError:
            # Empty repo with no commits
            return GitHistoryResult()

        if not commits:
            return GitHistoryResult()

        # Data structures for aggregation
        # contributor key: (name, email) -> {commit_count, files_touched, first_date, last_date}
        contributor_data: dict[tuple[str, str], dict] = {}
        # file path -> {change_count, contributors set}
        file_data: dict[str, dict] = defaultdict(lambda: {"change_count": 0, "contributors": set()})
        conventional_count = 0
        total_commits = len(commits)

        for commit in commits:
            author_key = (commit.author.name, commit.author.email)
            commit_date = commit.committed_datetime.strftime("%Y-%m-%d")

            # Update contributor data
            if author_key not in contributor_data:
                contributor_data[author_key] = {
                    "commit_count": 0,
                    "files_touched": set(),
                    "first_commit_date": commit_date,
                    "last_commit_date": commit_date,
                }

            contrib = contributor_data[author_key]
            contrib["commit_count"] += 1
            # Update date range (commits come newest-first from iter_commits)
            contrib["last_commit_date"] = max(contrib["last_commit_date"], commit_date)
            contrib["first_commit_date"] = min(contrib["first_commit_date"], commit_date)

            # Track files changed — skip merge commits with no stats gracefully
            try:
                for file_path in commit.stats.files:
                    contrib["files_touched"].add(file_path)
                    file_data[file_path]["change_count"] += 1
                    file_data[file_path]["contributors"].add(author_key)
            except (KeyError, TypeError):
                pass

            # Check conventional commit pattern
            message = commit.message.strip().split("\n")[0]
            if CONVENTIONAL_COMMIT_PATTERN.match(message):
                conventional_count += 1

        # Build Contributor objects sorted by commit_count desc
        contributors = sorted(
            [
                Contributor(
                    name=name,
                    email=email,
                    commit_count=data["commit_count"],
                    files_touched=sorted(data["files_touched"]),
                    first_commit_date=data["first_commit_date"],
                    last_commit_date=data["last_commit_date"],
                )
                for (name, email), data in contributor_data.items()
            ],
            key=lambda c: c.commit_count,
            reverse=True,
        )

        # Build HotFile objects — top 20 most changed files
        hot_files = sorted(
            [
                HotFile(
                    path=path,
                    change_count=data["change_count"],
                    unique_contributors=len(data["contributors"]),
                )
                for path, data in file_data.items()
            ],
            key=lambda f: f.change_count,
            reverse=True,
        )[:20]

        # Bus factor: minimum contributors to cover 50% of total commits
        bus_factor = self._calculate_bus_factor(contributors, total_commits)

        # Conventional commits ratio
        conventional_commits_ratio = (
            conventional_count / total_commits if total_commits > 0 else 0.0
        )

        # Commit frequency per week
        commit_frequency_per_week = self._calculate_commit_frequency(commits, total_commits)

        # Date range (commits are newest-first)
        last_commit_date = commits[0].committed_datetime.strftime("%Y-%m-%d")
        first_commit_date = commits[-1].committed_datetime.strftime("%Y-%m-%d")

        # Active branches
        active_branches = [ref.name for ref in repo.refs if isinstance(ref, git.Head)]

        return GitHistoryResult(
            total_commits=total_commits,
            contributors=contributors,
            hot_files=hot_files,
            bus_factor=bus_factor,
            conventional_commits_ratio=conventional_commits_ratio,
            commit_frequency_per_week=commit_frequency_per_week,
            first_commit_date=first_commit_date,
            last_commit_date=last_commit_date,
            active_branches=active_branches,
        )

    @staticmethod
    def _calculate_bus_factor(contributors: list[Contributor], total_commits: int) -> int:
        """Count minimum contributors needed to cover 50% of total commits."""
        if total_commits == 0:
            return 0

        threshold = total_commits * 0.5
        cumulative = 0
        for i, contrib in enumerate(contributors, start=1):
            cumulative += contrib.commit_count
            if cumulative >= threshold:
                return i
        return len(contributors)

    @staticmethod
    def _calculate_commit_frequency(commits: list, total_commits: int) -> float:
        """Calculate average commits per week over the repo's lifetime."""
        if total_commits <= 1:
            return float(total_commits)

        last_date = commits[0].committed_datetime
        first_date = commits[-1].committed_datetime
        span_days = (last_date - first_date).days

        if span_days == 0:
            return float(total_commits)

        weeks = span_days / 7.0
        return round(total_commits / weeks, 2)
