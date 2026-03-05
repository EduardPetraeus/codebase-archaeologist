# Codebase Archaeologist

An MCP server + CLI that analyzes any codebase and reverse-engineers its "institutional knowledge" — naming conventions, architecture patterns, knowledge silos, and tribal knowledge. Auto-generates CLAUDE.md, ARCHITECTURE.md, and ONBOARDING.md.

No LLM dependency. Pure heuristic analysis.

## Install

```bash
pip install codebase-archaeologist
```

Or from source:

```bash
git clone https://github.com/EduardPetraeus/codebase-archaeologist.git
cd codebase-archaeologist
pip install -e ".[dev]"
```

Requires Python 3.12+.

## CLI Usage

```bash
# Generate all docs to stdout
archaeologist dig ./my-repo

# Write docs to a directory
archaeologist dig ./my-repo -o ./output

# Generate only CLAUDE.md
archaeologist dig ./my-repo --docs claude-md

# JSON profile output
archaeologist dig ./my-repo --format json

# Skip git history analysis (faster)
archaeologist dig ./my-repo --no-git
```

### Sample Output

```
$ archaeologist dig ./codebase-archaeologist --docs claude-md

# CLAUDE.md — codebase-archaeologist

## project_context

project_name: "codebase-archaeologist"
description: "FastMCP application with CLI interface"
stack: "Python, FastMCP, click, gitpython, rich"
primary_language: "Python"

## conventions

naming:
  classes: PascalCase
  functions: snake_case

file_structure:
  source_code: src/
  tests: tests/

## verification

before_claiming_done:
  - Run tests: pytest
  - Lint: ruff
```

## MCP Server

### Tools

| Tool | Description |
|------|-------------|
| `analyze_codebase` | Full codebase profile — language, structure, patterns, git history |
| `explain_decision` | Explain architectural decisions based on codebase evidence |
| `generate_claude_md` | Generate the CLAUDE.md your repo should have had |
| `map_tribal_knowledge` | Map conventions, knowledge silos, risk areas, recommendations |

All tools are read-only.

### Setup with Claude Code

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "codebase-archaeologist": {
      "command": "python",
      "args": ["-m", "codebase_archaeologist.mcp_server"]
    }
  }
}
```

Or run directly:

```bash
python -m codebase_archaeologist.mcp_server
```

## What It Detects

**4 analyzers** feed into **3 generators**:

```
Git History ─────┐
Code Structure ──┤                  ┌─ CLAUDE.md
Pattern Detector ┼─→ Orchestrator ──┼─ ARCHITECTURE.md
Dependency ──────┘                  └─ ONBOARDING.md
```

| Analyzer | Detects |
|----------|---------|
| **Git History** | Contributors, hot files, bus factor, commit conventions, churn |
| **Code Structure** | Language, src layout, CI system, entry points, config files |
| **Pattern Detector** | Naming conventions, architecture patterns, type hints, docstrings |
| **Dependency** | Package manager, framework, dependency categories |

## v0.1 Limitations

- Deep analysis only for Python repos (other languages get basic structure)
- `explain_decision` is keyword-match + template (no LLM) — honest about it in output
- No monorepo support
- No incremental analysis / caching
- Git history capped at 1000 commits

## Development

```bash
pip install -e ".[dev]"
pytest                    # 96 tests
ruff check . && ruff format .
```

## License

MIT
