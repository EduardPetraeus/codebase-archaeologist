"""Detect naming conventions, architecture patterns, type hints, and docstrings."""

from __future__ import annotations

import ast
import re

from codebase_archaeologist.analyzers.base import BaseAnalyzer
from codebase_archaeologist.models import Convention, PatternResult

# Naming-convention regexes
_SNAKE_CASE = re.compile(r"^[a-z][a-z0-9_]*$")
_PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
_CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
_UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Directories that indicate specific architecture patterns
_LAYERED_DIRS = {"models", "views", "controllers", "services", "routes", "api"}
_MVC_MODEL = {"models"}
_MVC_VC = {"views", "controllers"}
_HEXAGONAL_DIRS = {"domain", "ports", "adapters"}


def _has_uppercase(name: str) -> bool:
    """Return True if name contains at least one uppercase letter."""
    return any(c.isupper() for c in name)


def _classify_name(name: str) -> str | None:
    """Classify a name into a naming convention category."""
    if _UPPER_SNAKE.match(name):
        return "UPPER_SNAKE"
    if _PASCAL_CASE.match(name):
        return "PascalCase"
    if _CAMEL_CASE.match(name) and _has_uppercase(name):
        return "camelCase"
    if _SNAKE_CASE.match(name):
        return "snake_case"
    return None


class PatternDetector(BaseAnalyzer):
    """Analyze Python source files for conventions, architecture, and quality patterns."""

    def analyze(self) -> PatternResult:
        """Run pattern detection across the repository."""
        python_files = self._collect_files(extensions={".py"})

        if not python_files:
            return PatternResult()

        # Accumulators
        function_names: list[str] = []
        class_names: list[str] = []
        total_functions = 0
        functions_with_hints = 0
        functions_with_docstrings = 0
        function_lengths: list[int] = []
        has_type_checking = False
        test_file_sources: list[str] = []
        has_conftest = False

        for filepath in python_files:
            try:
                source = filepath.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source, filename=str(filepath))
            except (SyntaxError, ValueError):
                continue

            # Check for TYPE_CHECKING / typing imports
            if not has_type_checking:
                if "if TYPE_CHECKING:" in source or "from typing import" in source:
                    has_type_checking = True

            # Conftest detection
            if filepath.name == "conftest.py":
                has_conftest = True

            # Collect test file sources for later analysis
            is_test_file = filepath.name.startswith("test_") or filepath.name.endswith("_test.py")
            if is_test_file:
                test_file_sources.append(source)

            # Walk the AST
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name
                    # Skip dunder methods
                    if not (name.startswith("__") and name.endswith("__")):
                        function_names.append(name)

                    total_functions += 1

                    # Return annotation
                    if node.returns is not None:
                        functions_with_hints += 1

                    # Docstring detection
                    if (
                        node.body
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)
                    ):
                        functions_with_docstrings += 1

                    # Function body length
                    if node.body:
                        first_line = node.body[0].lineno
                        last_line = node.body[-1].end_lineno or node.body[-1].lineno
                        function_lengths.append(last_line - first_line + 1)

                elif isinstance(node, ast.ClassDef):
                    class_names.append(node.name)

        # --- Build result ---
        result = PatternResult()
        result.has_type_checking = has_type_checking

        # Naming conventions
        result.naming_conventions = self._detect_naming_conventions(function_names, class_names)

        # Architecture patterns
        result.architecture_patterns = self._detect_architecture_patterns()

        # Test patterns
        result.test_patterns = self._detect_test_patterns(test_file_sources, has_conftest)

        # Ratios
        if total_functions > 0:
            result.type_hint_ratio = functions_with_hints / total_functions
            result.docstring_ratio = functions_with_docstrings / total_functions

        if function_lengths:
            result.avg_function_length = sum(function_lengths) / len(function_lengths)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_naming_conventions(
        self, function_names: list[str], class_names: list[str]
    ) -> list[Convention]:
        """Classify names and create conventions for dominant patterns."""
        conventions: list[Convention] = []

        # Function naming
        if function_names:
            fn_classes: dict[str, list[str]] = {}
            for name in function_names:
                cat = _classify_name(name)
                if cat:
                    fn_classes.setdefault(cat, []).append(name)

            total = len(function_names)
            for cat, names in fn_classes.items():
                ratio = len(names) / total
                if ratio > 0.80:
                    conventions.append(
                        Convention(
                            name=f"{cat} functions",
                            pattern=cat,
                            confidence=round(ratio, 2),
                            examples=names[:3],
                        )
                    )

        # Class naming
        if class_names:
            cls_classes: dict[str, list[str]] = {}
            for name in class_names:
                cat = _classify_name(name)
                if cat:
                    cls_classes.setdefault(cat, []).append(name)

            total = len(class_names)
            for cat, names in cls_classes.items():
                ratio = len(names) / total
                if ratio > 0.80:
                    conventions.append(
                        Convention(
                            name=f"{cat} classes",
                            pattern=cat,
                            confidence=round(ratio, 2),
                            examples=names[:3],
                        )
                    )

        return conventions

    def _detect_architecture_patterns(self) -> list[str]:
        """Detect architecture patterns based on directory structure."""
        patterns: list[str] = []

        # Collect top-level and nested directory names
        dir_names: set[str] = set()
        for path in self.repo_path.rglob("*"):
            if path.is_dir():
                dir_names.add(path.name)

        # Layered architecture
        if dir_names & _LAYERED_DIRS:
            patterns.append("layered")

        # MVC
        if _MVC_MODEL & dir_names and _MVC_VC & dir_names:
            patterns.append("MVC")

        # Hexagonal
        if _HEXAGONAL_DIRS <= dir_names:
            patterns.append("hexagonal")

        # Src layout
        if (self.repo_path / "src").is_dir():
            patterns.append("src-layout")

        # Monorepo: multiple pyproject.toml or package.json
        pyproject_count = len(list(self.repo_path.rglob("pyproject.toml")))
        package_json_count = len(list(self.repo_path.rglob("package.json")))
        if pyproject_count > 1 or package_json_count > 1:
            patterns.append("monorepo")

        return patterns

    def _detect_test_patterns(self, test_sources: list[str], has_conftest: bool) -> list[str]:
        """Detect testing patterns from test file sources."""
        patterns: list[str] = []

        all_test_source = "\n".join(test_sources)

        # pytest detection
        if "import pytest" in all_test_source or "from pytest" in all_test_source:
            patterns.append("pytest")
        elif test_sources:
            # Even without explicit pytest import, test functions suggest pytest
            for src in test_sources:
                if "def test_" in src:
                    patterns.append("pytest")
                    break

        # unittest detection
        if "unittest.TestCase" in all_test_source:
            patterns.append("unittest")

        # Fixtures
        if has_conftest:
            patterns.append("fixtures")

        # AAA pattern heuristic: test functions with blank line separations
        for src in test_sources:
            lines = src.split("\n")
            in_test = False
            blank_in_body = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("def test_"):
                    in_test = True
                    blank_in_body = False
                elif in_test:
                    if stripped == "":
                        blank_in_body = True
                    elif not stripped.startswith("def ") and blank_in_body:
                        patterns.append("AAA")
                        break
            if "AAA" in patterns:
                break

        return patterns
