"""Tests for ClaudeMdGenerator."""

from codebase_archaeologist.generators.claude_md_generator import ClaudeMdGenerator
from codebase_archaeologist.models import CodebaseProfile


class TestClaudeMdGenerator:
    """Tests for the CLAUDE.md generator."""

    def test_generates_valid_markdown(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert output.startswith("# CLAUDE.md")

    def test_includes_project_context(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert "project_context" in output

    def test_includes_project_name(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert "test-repo" in output

    def test_includes_stack(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert "Python" in output
        assert "FastAPI" in output

    def test_includes_conventions(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert "conventions" in output
        assert "snake_case" in output

    def test_includes_verification(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert "verification" in output
        assert "pytest" in output

    def test_includes_security(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile)
        output = gen.generate()
        assert "security" in output
        assert "never_commit" in output

    def test_minimal_style(self, sample_profile):
        gen = ClaudeMdGenerator(sample_profile, style="minimal")
        output = gen.generate()
        assert "project_context" in output
        assert "conventions" in output
        assert "security" not in output

    def test_handles_empty_profile(self):
        profile = CodebaseProfile()
        gen = ClaudeMdGenerator(profile)
        output = gen.generate()
        assert isinstance(output, str)
        assert len(output) > 0
        assert "# CLAUDE.md" in output
