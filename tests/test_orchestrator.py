"""Tests for the orchestrator."""

import pytest

from codebase_archaeologist.models import CodebaseProfile
from codebase_archaeologist.orchestrator import analyze_repo, dig, generate_docs


def test_analyze_repo(tmp_repo):
    profile = analyze_repo(tmp_repo)
    assert isinstance(profile, CodebaseProfile)
    assert profile.name == "test-repo"
    assert profile.code_structure.primary_language == "Python"
    assert profile.dependencies.package_manager == "pip"


def test_analyze_repo_no_git(tmp_repo):
    profile = analyze_repo(tmp_repo, include_git_history=False)
    assert profile.git_history.total_commits == 0


def test_analyze_repo_invalid_path():
    with pytest.raises(ValueError, match="Not a directory"):
        analyze_repo("/nonexistent/path")


def test_generate_docs(sample_profile):
    docs = generate_docs(sample_profile)
    assert "CLAUDE.md" in docs
    assert "ARCHITECTURE.md" in docs
    assert "ONBOARDING.md" in docs
    assert "# CLAUDE.md" in docs["CLAUDE.md"]


def test_generate_docs_selective(sample_profile):
    docs = generate_docs(sample_profile, docs=["claude-md"])
    assert "CLAUDE.md" in docs
    assert "ARCHITECTURE.md" not in docs


def test_dig(tmp_repo):
    results = dig(tmp_repo)
    assert len(results) == 3
    for name, content in results.items():
        assert name.endswith(".md")
        assert len(content) > 0


def test_dig_selective(tmp_repo):
    results = dig(tmp_repo, docs=["claude-md"])
    assert len(results) == 1
    assert "CLAUDE.md" in results
