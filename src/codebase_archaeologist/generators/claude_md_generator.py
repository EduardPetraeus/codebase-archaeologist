"""Generate CLAUDE.md files in the ai-agent-rules template format."""

from __future__ import annotations

from codebase_archaeologist.generators.base import BaseGenerator
from codebase_archaeologist.models import CodebaseProfile


class ClaudeMdGenerator(BaseGenerator):
    """Generate a CLAUDE.md file from a CodebaseProfile.

    Supports two styles:
    - "standard": full CLAUDE.md with all sections
    - "minimal": only project_context and conventions
    """

    def __init__(self, profile: CodebaseProfile, style: str = "standard") -> None:
        super().__init__(profile)
        if style not in ("standard", "minimal"):
            raise ValueError(f"Unknown style: {style!r}. Must be 'standard' or 'minimal'.")
        self.style = style

    def generate(self) -> str:
        """Return full CLAUDE.md content as a markdown string."""
        sections = [
            f"# CLAUDE.md — {self.profile.name or 'Unnamed Project'}",
            "",
            self._build_project_context(),
            "---",
            "",
            self._build_conventions(),
        ]

        if self.style == "standard":
            sections.extend(
                [
                    "---",
                    "",
                    self._build_verification(),
                    "---",
                    "",
                    self._build_security(),
                ]
            )

        return "\n".join(sections) + "\n"

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------

    def _build_project_context(self) -> str:
        """Build the project_context section."""
        p = self.profile
        structure = p.code_structure

        description = self._infer_description()
        stack = self._build_stack_string()
        primary_language = structure.primary_language or "unknown"

        lines = [
            "## project_context",
            "",
            f'project_name: "{p.name or "unknown"}"',
            f'description: "{description}"',
            f'stack: "{stack}"',
            f'primary_language: "{primary_language}"',
            "",
        ]
        return "\n".join(lines)

    def _build_conventions(self) -> str:
        """Build the conventions section."""
        patterns = self.profile.patterns
        structure = self.profile.code_structure

        # Detect naming conventions from analyzed patterns
        file_naming = "unknown"
        class_naming = "unknown"
        function_naming = "unknown"
        variable_naming = "unknown"

        for conv in patterns.naming_conventions:
            name_lower = conv.name.lower()
            pattern = conv.pattern
            if "function" in name_lower:
                function_naming = pattern
                variable_naming = pattern  # assume same as functions
            elif "class" in name_lower:
                class_naming = pattern
            elif "file" in name_lower:
                file_naming = pattern
            elif "variable" in name_lower:
                variable_naming = pattern

        # Detect source and test directories
        if structure.src_layout:
            source_dir = "src/"
        else:
            source_dir = "."

        test_dir = structure.test_directory or ("tests/" if structure.has_tests else "N/A")

        lines = [
            "## conventions",
            "",
            "naming:",
            f"  files: {file_naming}",
            f"  classes: {class_naming}",
            f"  functions: {function_naming}",
            f"  variables: {variable_naming}",
            "",
            "language: English",
            "",
            "file_structure:",
            f"  source_code: {source_dir}",
            f"  tests: {test_dir}",
            "",
        ]
        return "\n".join(lines)

    def _build_verification(self) -> str:
        """Build the verification section."""
        deps = self.profile.dependencies

        # Detect test runner
        test_runner = "pytest"
        for dep in deps.dev_dependencies:
            if dep.name in ("pytest", "unittest", "nose", "jest", "mocha", "vitest"):
                test_runner = dep.name
                break

        # Detect linter
        linter = "ruff"
        for dep in deps.dev_dependencies:
            if dep.name in ("ruff", "flake8", "pylint", "eslint", "biome"):
                linter = dep.name
                break

        lines = [
            "## verification",
            "",
            "before_claiming_done:",
            f"  - Run tests: {test_runner}",
            f"  - Lint: {linter}",
            "",
        ]
        return "\n".join(lines)

    def _build_security(self) -> str:
        """Build the security_protocol section."""
        lines = [
            "## security_protocol",
            "",
            "never_commit:",
            "  - API keys, tokens, secrets",
            "  - Passwords or credentials",
            "  - PII of any kind",
            "",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Inference helpers
    # ------------------------------------------------------------------

    def _infer_description(self) -> str:
        """Infer a project description from structure, framework, and entry points."""
        structure = self.profile.code_structure
        deps = self.profile.dependencies

        parts: list[str] = []

        # Framework hint
        if deps.framework:
            parts.append(f"{deps.framework} application")
        elif structure.primary_language and structure.primary_language != "unknown":
            parts.append(f"{structure.primary_language} project")
        else:
            parts.append("Software project")

        # Entry point hints
        entry_types = {ep.type for ep in structure.entry_points}
        if "cli" in entry_types:
            parts.append("with CLI interface")
        elif "server" in entry_types or "api" in entry_types:
            parts.append("with API server")

        return " ".join(parts)

    def _build_stack_string(self) -> str:
        """Combine primary language, framework, and key dependencies into a stack string."""
        structure = self.profile.code_structure
        deps = self.profile.dependencies

        components: list[str] = []

        # Primary language
        if structure.primary_language and structure.primary_language != "unknown":
            components.append(structure.primary_language)

        # Framework
        if deps.framework:
            components.append(deps.framework)

        # Key dependencies (skip framework if already included)
        for dep in deps.dependencies:
            if dep.name.lower() != deps.framework.lower() if deps.framework else False:
                components.append(dep.name)

        return ", ".join(components) if components else "unknown"
