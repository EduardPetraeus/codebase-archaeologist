"""Tests for data models."""

from pathlib import Path

from codebase_archaeologist.models import (
    CodebaseProfile,
    CodeStructureResult,
    ConfigFile,
    Contributor,
    Convention,
    Dependency,
    DependencyResult,
    EntryPoint,
    GitHistoryResult,
    HotFile,
)


def test_codebase_profile_defaults():
    profile = CodebaseProfile()
    assert profile.name == ""
    assert profile.git_history.total_commits == 0
    assert profile.code_structure.primary_language == "unknown"
    assert profile.patterns.naming_conventions == []
    assert profile.dependencies.dependencies == []


def test_codebase_profile_to_dict():
    profile = CodebaseProfile(
        path=Path("/tmp/test"),
        name="test",
        git_history=GitHistoryResult(total_commits=5),
        code_structure=CodeStructureResult(primary_language="Python"),
    )
    d = profile.to_dict()
    assert isinstance(d, dict)
    assert d["name"] == "test"
    assert d["path"] == "/tmp/test"
    assert d["git_history"]["total_commits"] == 5
    assert d["code_structure"]["primary_language"] == "Python"


def test_contributor_dataclass():
    c = Contributor(name="Alice", email="a@b.com", commit_count=10)
    assert c.name == "Alice"
    assert c.files_touched == []


def test_hot_file_dataclass():
    h = HotFile(path="main.py", change_count=5, unique_contributors=2)
    assert h.path == "main.py"
    assert h.last_modified == ""


def test_convention_dataclass():
    c = Convention(name="snake_case", pattern="snake_case", confidence=0.9)
    assert c.examples == []


def test_dependency_dataclass():
    d = Dependency(name="click", version_constraint=">=8.0", category="cli")
    assert d.name == "click"


def test_config_file_dataclass():
    cf = ConfigFile(path="pyproject.toml", type="pyproject.toml")
    assert cf.path == "pyproject.toml"


def test_entry_point_dataclass():
    ep = EntryPoint(path="main.py", type="cli")
    assert ep.description == ""


def test_to_dict_nested():
    profile = CodebaseProfile(
        path=Path("/tmp"),
        name="nested",
        dependencies=DependencyResult(
            dependencies=[Dependency(name="click", version_constraint=">=8.0", category="cli")]
        ),
    )
    d = profile.to_dict()
    assert len(d["dependencies"]["dependencies"]) == 1
    assert d["dependencies"]["dependencies"][0]["name"] == "click"
