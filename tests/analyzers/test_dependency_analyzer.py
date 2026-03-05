"""Tests for DependencyAnalyzer."""

from __future__ import annotations

import textwrap

import pytest

from codebase_archaeologist.analyzers.dependency_analyzer import DependencyAnalyzer


@pytest.fixture()
def tmp_repo(tmp_path):
    """Create a temporary repo with a pyproject.toml containing typical dependencies."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        textwrap.dedent("""\
            [project]
            name = "example"
            requires-python = ">=3.12"
            dependencies = [
                "click>=8.0",
                "requests>=2.28",
                "sqlalchemy>=2.0",
            ]

            [project.optional-dependencies]
            dev = [
                "pytest>=7.0",
                "ruff>=0.1",
            ]
        """)
    )
    return tmp_path


def test_detects_pip_package_manager(tmp_repo):
    analyzer = DependencyAnalyzer(repo_path=tmp_repo)
    result = analyzer.analyze()
    assert result.package_manager == "pip"


def test_parses_dependencies(tmp_repo):
    analyzer = DependencyAnalyzer(repo_path=tmp_repo)
    result = analyzer.analyze()
    dep_names = [d.name for d in result.dependencies]
    assert "click" in dep_names
    assert "requests" in dep_names
    assert "sqlalchemy" in dep_names


def test_parses_dev_dependencies(tmp_repo):
    analyzer = DependencyAnalyzer(repo_path=tmp_repo)
    result = analyzer.analyze()
    dev_names = [d.name for d in result.dev_dependencies]
    assert "pytest" in dev_names
    assert "ruff" in dev_names


def test_categorizes_dependencies(tmp_repo):
    analyzer = DependencyAnalyzer(repo_path=tmp_repo)
    result = analyzer.analyze()
    assert "click" in result.tech_categories.get("cli", [])
    assert "sqlalchemy" in result.tech_categories.get("database", [])


def test_detects_python_version(tmp_repo):
    analyzer = DependencyAnalyzer(repo_path=tmp_repo)
    result = analyzer.analyze()
    assert result.python_version == ">=3.12"


def test_no_config_returns_empty(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    analyzer = DependencyAnalyzer(repo_path=empty_dir)
    result = analyzer.analyze()
    assert result.dependencies == []
    assert result.dev_dependencies == []
    assert result.package_manager == ""
    assert result.python_version == ""
    assert result.framework == ""
    assert result.tech_categories == {}


def test_requirements_txt_fallback(tmp_path):
    req_dir = tmp_path / "req_project"
    req_dir.mkdir()
    (req_dir / "requirements.txt").write_text("requests==2.28.0\nflask>=2.0\n")

    analyzer = DependencyAnalyzer(repo_path=req_dir)
    result = analyzer.analyze()

    assert result.package_manager == "pip"
    dep_names = [d.name for d in result.dependencies]
    assert "requests" in dep_names
    assert "flask" in dep_names

    # Verify version parsing
    versions = {d.name: d.version_constraint for d in result.dependencies}
    assert versions["requests"] == "==2.28.0"
    assert versions["flask"] == ">=2.0"


def test_framework_detection(tmp_path):
    proj_dir = tmp_path / "fastapi_project"
    proj_dir.mkdir()
    (proj_dir / "pyproject.toml").write_text(
        textwrap.dedent("""\
            [project]
            name = "api"
            dependencies = [
                "fastapi>=0.100",
            ]
        """)
    )

    analyzer = DependencyAnalyzer(repo_path=proj_dir)
    result = analyzer.analyze()

    assert result.framework == "FastAPI"
