"""CLI interface — `archaeologist dig`."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

from codebase_archaeologist.orchestrator import analyze_repo, dig

console = Console()


@click.group()
@click.version_option(package_name="codebase-archaeologist")
def cli():
    """Codebase Archaeologist — reverse-engineer institutional knowledge from codebases."""


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="Output directory for docs.")
@click.option(
    "--docs",
    type=click.Choice(["claude-md", "architecture", "onboarding"]),
    multiple=True,
    help="Which docs to generate. Default: all.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format.",
)
@click.option("--style", type=click.Choice(["standard", "minimal"]), default="standard")
@click.option("--no-git", is_flag=True, help="Skip git history analysis.")
@click.option("--max-files", type=int, default=500, help="Max files to analyze.")
@click.option("--max-commits", type=int, default=1000, help="Max git commits to analyze.")
def dig_cmd(path, output, docs, output_format, style, no_git, max_files, max_commits):
    """Analyze a codebase and generate documentation."""
    repo_path = Path(path)
    console.print(f"\n[bold]Analyzing:[/bold] {repo_path.name}", style="cyan")

    docs_list = list(docs) if docs else None

    if output_format == "json":
        profile = analyze_repo(
            repo_path,
            include_git_history=not no_git,
            max_files=max_files,
            max_commits=max_commits,
        )
        result = profile.to_dict()
        if output:
            out_dir = Path(output)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "profile.json"
            out_file.write_text(json.dumps(result, indent=2, default=str))
            console.print(f"[green]Written:[/green] {out_file}")
        else:
            console.print_json(json.dumps(result, default=str))
        return

    results = dig(
        repo_path,
        docs=docs_list,
        style=style,
        include_git_history=not no_git,
        max_files=max_files,
        max_commits=max_commits,
    )

    if output:
        out_dir = Path(output)
        out_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in results.items():
            out_file = out_dir / filename
            out_file.write_text(content)
            console.print(f"[green]Written:[/green] {out_file}")
    else:
        for filename, content in results.items():
            console.print(Panel(content, title=filename, border_style="blue"))

    console.print(f"\n[bold green]Done![/bold green] Generated {len(results)} document(s).\n")
