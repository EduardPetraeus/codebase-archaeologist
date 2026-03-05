"""Tests for the CLI."""

from click.testing import CliRunner

from codebase_archaeologist.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Codebase Archaeologist" in result.output


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_dig_command(tmp_repo):
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", str(tmp_repo)])
    assert result.exit_code == 0
    assert "Done!" in result.output


def test_dig_with_output(tmp_repo, tmp_path):
    out_dir = tmp_path / "output"
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", str(tmp_repo), "-o", str(out_dir)])
    assert result.exit_code == 0
    assert (out_dir / "CLAUDE.md").exists()
    assert (out_dir / "ARCHITECTURE.md").exists()
    assert (out_dir / "ONBOARDING.md").exists()


def test_dig_selective_doc(tmp_repo):
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", str(tmp_repo), "--docs", "claude-md"])
    assert result.exit_code == 0
    assert "CLAUDE.md" in result.output


def test_dig_json_format(tmp_repo):
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", str(tmp_repo), "--format", "json"])
    assert result.exit_code == 0


def test_dig_no_git(tmp_repo):
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", str(tmp_repo), "--no-git"])
    assert result.exit_code == 0


def test_dig_minimal_style(tmp_repo):
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", str(tmp_repo), "--style", "minimal"])
    assert result.exit_code == 0


def test_dig_invalid_path():
    runner = CliRunner()
    result = runner.invoke(cli, ["dig", "/nonexistent/path"])
    assert result.exit_code != 0
