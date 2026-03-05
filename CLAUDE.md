# Codebase Archaeologist — Agent Rules

## Project Overview
MCP server + CLI that reverse-engineers institutional knowledge from codebases.
Deep research project: `~/deep-research/active/codebase-archaeologist/BRIEF.md`

## Stack
- Python 3.12+
- MCP SDK (Model Context Protocol)
- Click (CLI framework)
- GitPython (git history analysis)

## Code Style
- `snake_case` for variables/functions/modules
- `kebab-case` for files/directories
- `PascalCase` for classes
- All code, comments, and docs in English

## Architecture
- `src/codebase_archaeologist/` — main package
  - `mcp_server.py` — MCP server with analysis tools
  - `cli.py` — Click CLI entry point
  - `analyzers/` — individual analysis modules
  - `generators/` — document generators (CLAUDE.md, ARCHITECTURE.md, etc.)
- `tests/` — pytest test suite

## Development
```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format .
```
