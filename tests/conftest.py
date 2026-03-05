"""Shared test fixtures."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary git repo with basic Python project structure."""
    repo = tmp_path / "test-repo"
    repo.mkdir()

    # Init git
    subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=repo, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=repo, capture_output=True, check=True
    )

    # Create Python project structure
    src = repo / "src" / "myproject"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text('__version__ = "0.1.0"\n')
    (src / "main.py").write_text(
        "def main():\n"
        '    """Entry point."""\n'
        '    print("hello")\n\n\n'
        'if __name__ == "__main__":\n'
        "    main()\n"
    )
    (src / "utils.py").write_text(
        "def helper_function(value: int) -> str:\n"
        '    """Convert value to string."""\n'
        "    return str(value)\n"
    )
    (src / "models.py").write_text(
        "from dataclasses import dataclass\n\n\n"
        "@dataclass\nclass User:\n    name: str\n    email: str\n"
    )

    # Tests
    tests = repo / "tests"
    tests.mkdir()
    (tests / "__init__.py").write_text("")
    (tests / "test_main.py").write_text(
        "from myproject.main import main\n\n\ndef test_main():\n    main()\n"
    )

    # Config files
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "myproject"\nversion = "0.1.0"\n'
        'requires-python = ">=3.12"\n'
        "dependencies = [\n"
        '    "click>=8.0",\n'
        '    "requests>=2.28",\n'
        '    "sqlalchemy>=2.0",\n'
        "]\n\n"
        "[project.optional-dependencies]\n"
        'dev = ["pytest>=7.0", "ruff>=0.4.0"]\n'
    )
    (repo / "README.md").write_text("# My Project\n\nA test project.\n")

    # CI
    ci = repo / ".github" / "workflows"
    ci.mkdir(parents=True)
    (ci / "ci.yml").write_text("name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest\n")

    # Initial commit
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: initial project structure"],
        cwd=repo,
        capture_output=True,
        check=True,
    )

    return repo


@pytest.fixture
def tmp_repo_with_history(tmp_repo):
    """Extend tmp_repo with multiple commits and contributors."""
    # Second commit
    (tmp_repo / "src" / "myproject" / "api.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
        '@app.get("/health")\ndef health():\n    return {"status": "ok"}\n'
    )
    subprocess.run(["git", "add", "."], cwd=tmp_repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "feat(api): add health endpoint"],
        cwd=tmp_repo,
        capture_output=True,
        check=True,
    )

    # Third commit by different author
    (tmp_repo / "src" / "myproject" / "utils.py").write_text(
        "def helper_function(value: int) -> str:\n"
        '    """Convert value to string."""\n'
        "    return str(value)\n\n\n"
        "def format_name(first: str, last: str) -> str:\n"
        '    """Format full name."""\n'
        '    return f"{first} {last}"\n'
    )
    subprocess.run(["git", "add", "."], cwd=tmp_repo, capture_output=True, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Jane Dev",
            "-c",
            "user.email=jane@dev.com",
            "commit",
            "-m",
            "feat(utils): add format_name helper",
        ],
        cwd=tmp_repo,
        capture_output=True,
        check=True,
    )

    # Fourth commit — modify existing file
    (tmp_repo / "src" / "myproject" / "main.py").write_text(
        "import sys\n\n\n"
        "def main():\n"
        '    """Entry point."""\n'
        '    print("hello", file=sys.stdout)\n'
        "    return 0\n\n\n"
        'if __name__ == "__main__":\n'
        "    sys.exit(main())\n"
    )
    subprocess.run(["git", "add", "."], cwd=tmp_repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "refactor(main): improve exit handling"],
        cwd=tmp_repo,
        capture_output=True,
        check=True,
    )

    return tmp_repo


@pytest.fixture
def sample_profile():
    """Create a sample CodebaseProfile for generator tests."""
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
        PatternResult,
    )

    return CodebaseProfile(
        path=Path("/tmp/test-repo"),
        name="test-repo",
        git_history=GitHistoryResult(
            total_commits=42,
            contributors=[
                Contributor(
                    name="Alice",
                    email="alice@test.com",
                    commit_count=30,
                    files_touched=["src/main.py", "src/utils.py"],
                    first_commit_date="2024-01-01",
                    last_commit_date="2024-06-01",
                ),
                Contributor(
                    name="Bob",
                    email="bob@test.com",
                    commit_count=12,
                    files_touched=["tests/test_main.py"],
                    first_commit_date="2024-03-01",
                    last_commit_date="2024-06-01",
                ),
            ],
            hot_files=[
                HotFile(path="src/main.py", change_count=15, unique_contributors=2),
                HotFile(path="src/utils.py", change_count=8, unique_contributors=1),
            ],
            bus_factor=2,
            conventional_commits_ratio=0.85,
            commit_frequency_per_week=3.5,
            first_commit_date="2024-01-01",
            last_commit_date="2024-06-01",
        ),
        code_structure=CodeStructureResult(
            primary_language="Python",
            languages={"Python": 10, "YAML": 2},
            total_files=12,
            total_lines=500,
            src_layout=True,
            has_tests=True,
            test_directory="tests/",
            has_ci=True,
            ci_system="GitHub Actions",
            config_files=[ConfigFile(path="pyproject.toml", type="pyproject.toml")],
            entry_points=[EntryPoint(path="src/main.py", type="cli", description="CLI entry")],
        ),
        patterns=PatternResult(
            naming_conventions=[
                Convention(
                    name="snake_case functions",
                    pattern="snake_case",
                    confidence=0.95,
                    examples=["helper_function", "format_name"],
                ),
                Convention(
                    name="PascalCase classes",
                    pattern="PascalCase",
                    confidence=0.9,
                    examples=["User", "DataProcessor"],
                ),
            ],
            architecture_patterns=["layered"],
            test_patterns=["pytest", "fixtures"],
            type_hint_ratio=0.8,
            docstring_ratio=0.6,
            avg_function_length=8.5,
        ),
        dependencies=DependencyResult(
            package_manager="pip",
            framework="FastAPI",
            framework_version=">=0.100",
            dependencies=[
                Dependency(name="click", version_constraint=">=8.0", category="cli"),
                Dependency(name="requests", version_constraint=">=2.28", category="http"),
                Dependency(name="sqlalchemy", version_constraint=">=2.0", category="database"),
            ],
            dev_dependencies=[
                Dependency(name="pytest", version_constraint=">=7.0", category="testing"),
                Dependency(name="ruff", version_constraint=">=0.4.0", category="linting"),
            ],
            python_version=">=3.12",
            tech_categories={
                "cli": ["click"],
                "http": ["requests"],
                "database": ["sqlalchemy"],
                "testing": ["pytest"],
                "linting": ["ruff"],
            },
        ),
    )
