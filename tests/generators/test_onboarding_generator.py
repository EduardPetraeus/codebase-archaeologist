"""Tests for OnboardingGenerator."""

from codebase_archaeologist.generators.onboarding_generator import OnboardingGenerator
from codebase_archaeologist.models import CodebaseProfile


class TestOnboardingGenerator:
    """Tests for OnboardingGenerator using the sample_profile fixture."""

    def test_generates_valid_markdown(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert output.startswith("# Onboarding")

    def test_includes_quick_start(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "Quick Start" in output

    def test_includes_setup_commands(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "pip install" in output

    def test_includes_test_command(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "pytest" in output

    def test_includes_conventions(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "snake_case" in output

    def test_includes_entry_points(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "main.py" in output or "Where to Start" in output

    def test_includes_contributors(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "Alice" in output

    def test_handles_empty_profile(self):
        empty_profile = CodebaseProfile()
        gen = OnboardingGenerator(empty_profile)
        output = gen.generate()
        assert "# Onboarding" in output
        assert len(output) > 0

    def test_includes_project_name(self, sample_profile):
        gen = OnboardingGenerator(sample_profile)
        output = gen.generate()
        assert "test-repo" in output
