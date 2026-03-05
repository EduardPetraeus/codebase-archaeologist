"""Tests for the MCP server tools."""

from codebase_archaeologist.mcp_server import (
    _extract_keywords,
    analyze_codebase,
    explain_decision,
    generate_claude_md,
    map_tribal_knowledge,
)


def test_analyze_codebase(tmp_repo):
    result = analyze_codebase(str(tmp_repo))
    assert isinstance(result, dict)
    assert result["name"] == "test-repo"
    assert "git_history" in result
    assert "code_structure" in result


def test_analyze_codebase_no_git(tmp_repo):
    result = analyze_codebase(str(tmp_repo), include_git_history=False)
    assert result["git_history"]["total_commits"] == 0


def test_explain_decision(tmp_repo):
    result = explain_decision(str(tmp_repo), "Why click?")
    assert isinstance(result, str)
    assert "Analysis" in result


def test_explain_decision_no_match(tmp_repo):
    result = explain_decision(str(tmp_repo), "Why quantum computing?")
    assert "No Direct Evidence" in result


def test_generate_claude_md(tmp_repo):
    result = generate_claude_md(str(tmp_repo))
    assert isinstance(result, str)
    assert "CLAUDE.md" in result


def test_generate_claude_md_minimal(tmp_repo):
    result = generate_claude_md(str(tmp_repo), style="minimal")
    assert isinstance(result, str)


def test_map_tribal_knowledge(tmp_repo):
    result = map_tribal_knowledge(str(tmp_repo))
    assert isinstance(result, dict)
    assert "conventions" in result
    assert "knowledge_silos" in result
    assert "risk_areas" in result
    assert "recommendations" in result
    assert result["project"] == "test-repo"


def test_extract_keywords():
    assert "fastapi" in _extract_keywords("Why use FastAPI?")
    assert "the" not in _extract_keywords("Why is the framework chosen?")
    assert len(_extract_keywords("")) == 0
