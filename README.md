# Codebase Archaeologist

An MCP server + CLI that analyzes any codebase and reverse-engineers its "institutional knowledge" — not just code structure, but *why* decisions were made, tech debt patterns, tribal knowledge, and onboarding guides.

## What It Does

- **Git history analysis:** Who changed what, when, and (inferred) why
- **Pattern detection:** "This repo uses Repository pattern", "Tests follow AAA"
- **Knowledge extraction:** Architecture decisions, coding conventions, tribal knowledge
- **Auto-generated docs:** CLAUDE.md + ARCHITECTURE.md + ONBOARDING.md

## MCP Server Tools

| Tool | Description |
|------|-------------|
| `analyze_codebase` | Full codebase analysis with pattern detection |
| `explain_decision` | Explain why a specific architectural decision was made |
| `generate_claude_md` | Generate the CLAUDE.md that should have existed |
| `map_tribal_knowledge` | Map undocumented conventions and tribal knowledge |

## CLI Usage

```bash
archaeologist dig ./my-repo
```

Produces a full report with generated documentation.

## Why This Exists

Every time a developer opens an unfamiliar codebase, they spend 20+ minutes understanding context. Existing tools (CodeScene, etc.) measure metrics. None *explain* a codebase the way a senior developer would. This tool does.

## Status

Early development. See [BRIEF.md](~/deep-research/active/codebase-archaeologist/BRIEF.md) for project plan.

## License

MIT
