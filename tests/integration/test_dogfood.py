"""Integration test: run codebase-archaeologist on itself."""

from pathlib import Path

from codebase_archaeologist.orchestrator import analyze_repo, dig

REPO_ROOT = Path(__file__).parent.parent.parent


def test_analyze_self():
    """Analyze our own repo — must not crash."""
    profile = analyze_repo(REPO_ROOT)
    assert profile.name == "codebase-archaeologist"
    assert profile.code_structure.primary_language == "Python"
    assert profile.code_structure.src_layout is True
    assert profile.code_structure.has_tests is True
    assert profile.dependencies.package_manager == "pip"
    assert profile.git_history.total_commits > 0


def test_dig_self():
    """Generate docs for our own repo — must produce valid output."""
    results = dig(REPO_ROOT)
    assert len(results) == 3

    claude_md = results["CLAUDE.md"]
    assert "codebase-archaeologist" in claude_md
    assert "Python" in claude_md

    arch = results["ARCHITECTURE.md"]
    assert "codebase-archaeologist" in arch

    onboarding = results["ONBOARDING.md"]
    assert "codebase-archaeologist" in onboarding


def test_analyze_self_no_git():
    """Analyze without git history — still produces useful output."""
    profile = analyze_repo(REPO_ROOT, include_git_history=False)
    assert profile.code_structure.primary_language == "Python"
    assert profile.git_history.total_commits == 0
