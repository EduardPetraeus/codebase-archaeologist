"""Dependency analyzer — parses package manager files for deps and frameworks."""

from __future__ import annotations

import json
import re
import tomllib
from configparser import ConfigParser
from pathlib import Path

from codebase_archaeologist.analyzers.base import BaseAnalyzer
from codebase_archaeologist.models import Dependency, DependencyResult

# Framework name mapping: dependency name -> display name
_FRAMEWORK_MAP: dict[str, str] = {
    # Python
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "starlette": "Starlette",
    "tornado": "Tornado",
    "fastmcp": "FastMCP",
    # JavaScript
    "react": "React",
    "next": "Next.js",
    "vue": "Vue",
    "angular": "Angular",
    "express": "Express",
    "nestjs": "NestJS",
}

# Category mapping: category -> set of dependency names
_CATEGORY_MAP: dict[str, set[str]] = {
    "web": {"fastapi", "flask", "django", "starlette", "express", "uvicorn", "gunicorn"},
    "http": {"requests", "httpx", "aiohttp", "urllib3"},
    "database": {"sqlalchemy", "psycopg2", "pymongo", "redis", "motor", "prisma"},
    "cli": {"click", "typer", "argparse", "rich"},
    "testing": {"pytest", "unittest", "jest", "mocha", "nose"},
    "linting": {"ruff", "flake8", "pylint", "eslint", "black", "mypy"},
    "data": {"pandas", "numpy", "polars", "duckdb", "pyspark"},
    "auth": {"pyjwt", "passlib", "python-jose", "bcrypt"},
    "mcp": {"fastmcp", "mcp"},
}


class DependencyAnalyzer(BaseAnalyzer):
    """Analyzes package manager files to extract dependency information."""

    def analyze(self) -> DependencyResult:
        """Run dependency analysis on the repository root."""
        dependencies: list[Dependency] = []
        dev_dependencies: list[Dependency] = []
        package_manager = ""
        python_version = ""
        framework = ""
        framework_version = ""
        tech_categories: dict[str, list[str]] = {}

        root = Path(self.repo_path)

        # --- Try pyproject.toml first ---
        pyproject_path = root / "pyproject.toml"
        if pyproject_path.exists():
            package_manager = "pip"
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            project = data.get("project", {})

            # Main dependencies
            for spec in project.get("dependencies", []):
                name, version = self._parse_pep508(spec)
                dependencies.append(Dependency(name=name, version_constraint=version))

            # Optional / dev dependencies
            for group_deps in project.get("optional-dependencies", {}).values():
                for spec in group_deps:
                    name, version = self._parse_pep508(spec)
                    dev_dependencies.append(Dependency(name=name, version_constraint=version))

            # Python version
            python_version = project.get("requires-python")

        # --- setup.cfg fallback ---
        elif (root / "setup.cfg").exists():
            package_manager = "pip"
            cfg = ConfigParser()
            cfg.read(root / "setup.cfg")
            if cfg.has_option("options", "install_requires"):
                for spec in cfg.get("options", "install_requires").strip().splitlines():
                    spec = spec.strip()
                    if spec:
                        name, version = self._parse_pep508(spec)
                        dependencies.append(Dependency(name=name, version_constraint=version))
            if cfg.has_option("options", "python_requires"):
                python_version = cfg.get("options", "python_requires").strip()

        # --- requirements.txt fallback ---
        elif (root / "requirements.txt").exists():
            package_manager = "pip"
            with open(root / "requirements.txt") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    name, version = self._parse_pep508(line)
                    dependencies.append(Dependency(name=name, version_constraint=version))

        # --- package.json ---
        pkg_json_path = root / "package.json"
        if pkg_json_path.exists():
            if not package_manager:
                package_manager = "npm"
            with open(pkg_json_path) as f:
                pkg = json.loads(f.read())
            for name, version in pkg.get("dependencies", {}).items():
                dependencies.append(Dependency(name=name, version_constraint=version))
            for name, version in pkg.get("devDependencies", {}).items():
                dev_dependencies.append(Dependency(name=name, version_constraint=version))

        # --- Cargo.toml detection ---
        if (root / "Cargo.toml").exists() and not package_manager:
            package_manager = "cargo"

        # --- Framework detection (pick the first match) ---
        all_deps = dependencies + dev_dependencies
        for dep in all_deps:
            if framework:
                break
            normalized = dep.name.lower().replace("-", "").replace("_", "")
            for key, display_name in _FRAMEWORK_MAP.items():
                if normalized == key.replace("-", "").replace("_", ""):
                    framework = display_name
                    framework_version = dep.version_constraint
                    break

        # --- Categorize dependencies ---
        for dep in all_deps:
            normalized = dep.name.lower().replace("-", "_")
            base_name = normalized.split("-")[0] if "-" in dep.name else normalized
            for category, names in _CATEGORY_MAP.items():
                if normalized in names or base_name in names:
                    dep.category = category
                    tech_categories.setdefault(category, [])
                    if dep.name not in tech_categories[category]:
                        tech_categories[category].append(dep.name)
                    break

        return DependencyResult(
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            package_manager=package_manager,
            python_version=python_version or "",
            framework=framework,
            framework_version=framework_version,
            tech_categories=tech_categories,
        )

    @staticmethod
    def _parse_pep508(spec: str) -> tuple[str, str]:
        """Parse a PEP 508 dependency string into (name, version_constraint).

        Examples:
            "click>=8.0"        -> ("click", ">=8.0")
            "package[extra]>=1.0" -> ("package", ">=1.0")
            "requests"          -> ("requests", "")
        """
        spec = spec.strip()

        # Remove extras like [extra1,extra2]
        spec = re.sub(r"\[.*?\]", "", spec)

        # Split on first version operator
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*(.*)", spec)
        if not match:
            return spec, ""

        name = match.group(1).strip()
        version = match.group(2).strip()

        # Remove any trailing comments or environment markers after ;
        if ";" in version:
            version = version.split(";")[0].strip()

        return name, version
