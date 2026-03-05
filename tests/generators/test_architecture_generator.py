"""Tests for ArchitectureGenerator."""

from codebase_archaeologist.generators.architecture_generator import ArchitectureGenerator
from codebase_archaeologist.models import (
    CodebaseProfile,
    GitHistoryResult,
)


class TestArchitectureGenerator:
    """Tests for ARCHITECTURE.md generation."""

    def test_generates_valid_markdown(self, sample_profile):
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert output.startswith("# Architecture")

    def test_includes_tech_stack(self, sample_profile):
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert "Tech Stack" in output
        assert "Python" in output

    def test_includes_framework(self, sample_profile):
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert "FastAPI" in output

    def test_includes_directory_structure(self, sample_profile):
        # Add directory tree data so the section is generated
        sample_profile.code_structure.directory_tree = {
            "src": ["myproject"],
            "tests": ["test_main.py"],
        }
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert "Directory" in output

    def test_includes_entry_points(self, sample_profile):
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert "Entry Point" in output

    def test_includes_hot_files(self, sample_profile):
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert "Hot File" in output
        assert "main.py" in output

    def test_includes_bus_factor(self, sample_profile):
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        assert "bus factor" in output.lower()

    def test_handles_empty_profile(self):
        profile = CodebaseProfile()
        gen = ArchitectureGenerator(profile)
        output = gen.generate()
        # Should not crash, and should still produce a header
        assert "# Architecture" in output

    def test_handles_no_git_history(self, sample_profile):
        sample_profile.git_history = GitHistoryResult(total_commits=0)
        gen = ArchitectureGenerator(sample_profile)
        output = gen.generate()
        # Hot files section should be absent
        assert "Hot File" not in output
        # Knowledge risks section should be absent
        assert "Knowledge Risks" not in output
        # Rest of the document should still work
        assert "Tech Stack" in output
