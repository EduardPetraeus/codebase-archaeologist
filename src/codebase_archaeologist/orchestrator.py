"""Orchestrator — runs all analyzers and feeds results to generators."""

from pathlib import Path

from codebase_archaeologist.analyzers.code_structure import CodeStructureAnalyzer
from codebase_archaeologist.analyzers.dependency_analyzer import DependencyAnalyzer
from codebase_archaeologist.analyzers.git_history import GitHistoryAnalyzer
from codebase_archaeologist.analyzers.pattern_detector import PatternDetector
from codebase_archaeologist.generators.architecture_generator import ArchitectureGenerator
from codebase_archaeologist.generators.claude_md_generator import ClaudeMdGenerator
from codebase_archaeologist.generators.onboarding_generator import OnboardingGenerator
from codebase_archaeologist.models import CodebaseProfile


def analyze_repo(
    path: str | Path,
    include_git_history: bool = True,
    max_files: int = 500,
    max_commits: int = 1000,
) -> CodebaseProfile:
    """Run all analyzers on a repository and return a CodebaseProfile."""
    repo_path = Path(path).resolve()
    if not repo_path.is_dir():
        raise ValueError(f"Not a directory: {repo_path}")

    profile = CodebaseProfile(
        path=repo_path,
        name=repo_path.name,
    )

    profile.code_structure = CodeStructureAnalyzer(repo_path, max_files=max_files).analyze()
    profile.dependencies = DependencyAnalyzer(repo_path, max_files=max_files).analyze()
    profile.patterns = PatternDetector(repo_path, max_files=max_files).analyze()

    if include_git_history:
        profile.git_history = GitHistoryAnalyzer(
            repo_path, max_files=max_files, max_commits=max_commits
        ).analyze()

    return profile


def generate_docs(
    profile: CodebaseProfile,
    docs: list[str] | None = None,
    style: str = "standard",
) -> dict[str, str]:
    """Generate documentation from a CodebaseProfile.

    Args:
        profile: Analyzed codebase profile.
        docs: Which docs to generate. None means all.
              Options: "claude-md", "architecture", "onboarding"
        style: Style for CLAUDE.md generation.

    Returns:
        Dict mapping doc name to markdown content.
    """
    if docs is None:
        docs = ["claude-md", "architecture", "onboarding"]

    result = {}

    if "claude-md" in docs:
        result["CLAUDE.md"] = ClaudeMdGenerator(profile, style=style).generate()
    if "architecture" in docs:
        result["ARCHITECTURE.md"] = ArchitectureGenerator(profile).generate()
    if "onboarding" in docs:
        result["ONBOARDING.md"] = OnboardingGenerator(profile).generate()

    return result


def dig(
    path: str | Path,
    docs: list[str] | None = None,
    style: str = "standard",
    include_git_history: bool = True,
    max_files: int = 500,
    max_commits: int = 1000,
) -> dict[str, str]:
    """Full pipeline: analyze repo and generate docs."""
    profile = analyze_repo(
        path,
        include_git_history=include_git_history,
        max_files=max_files,
        max_commits=max_commits,
    )
    return generate_docs(profile, docs=docs, style=style)
