"""MCP server with 4 tools for codebase analysis."""

import re

from fastmcp import FastMCP

from codebase_archaeologist.orchestrator import analyze_repo, generate_docs

mcp = FastMCP(
    "Codebase Archaeologist",
    instructions="Reverse-engineer institutional knowledge from codebases",
)


@mcp.tool()
def analyze_codebase(
    path: str,
    include_git_history: bool = True,
    max_files: int = 500,
) -> dict:
    """Analyze a codebase and return a full profile.

    Args:
        path: Path to the repository root.
        include_git_history: Whether to analyze git history.
        max_files: Maximum files to sample.

    Returns:
        Full CodebaseProfile as a dictionary.
    """
    profile = analyze_repo(path, include_git_history=include_git_history, max_files=max_files)
    return profile.to_dict()


@mcp.tool()
def explain_decision(path: str, question: str) -> str:
    """Explain an architectural decision based on codebase evidence.

    This is a heuristic-based explanation (no LLM). It searches git history,
    file structure, and dependencies for evidence related to the question.

    Args:
        path: Path to the repository root.
        question: The question about the codebase (e.g. "Why FastAPI?", "Why src layout?")

    Returns:
        Markdown explanation with evidence.
    """
    profile = analyze_repo(path, include_git_history=True, max_files=500)
    keywords = _extract_keywords(question)
    evidence = []

    # Search in dependencies
    for dep in profile.dependencies.dependencies:
        if any(kw in dep.name.lower() for kw in keywords):
            evidence.append(
                f"- **Dependency found:** `{dep.name}` ({dep.version_constraint}) "
                f"in category '{dep.category}'"
            )

    if profile.dependencies.framework:
        fw_lower = profile.dependencies.framework.lower()
        if any(kw in fw_lower for kw in keywords):
            evidence.append(
                f"- **Framework:** {profile.dependencies.framework} "
                f"{profile.dependencies.framework_version}"
            )

    # Search in structure
    if any(kw in ("src", "layout", "structure", "directory") for kw in keywords):
        if profile.code_structure.src_layout:
            evidence.append("- **Layout:** Uses `src/` layout (modern Python packaging convention)")

    if any(kw in ("test", "testing", "tests") for kw in keywords):
        if profile.code_structure.has_tests:
            evidence.append(f"- **Tests:** Found in `{profile.code_structure.test_directory}`")
        for pattern in profile.patterns.test_patterns:
            evidence.append(f"- **Test pattern:** {pattern}")

    if any(kw in ("ci", "cd", "pipeline", "actions", "github") for kw in keywords):
        if profile.code_structure.has_ci:
            evidence.append(f"- **CI/CD:** {profile.code_structure.ci_system}")

    # Search in patterns
    for pattern in profile.patterns.architecture_patterns:
        if any(kw in pattern.lower() for kw in keywords):
            evidence.append(f"- **Architecture pattern:** {pattern}")

    # Search in git history
    for contrib in profile.git_history.contributors[:5]:
        if any(kw in contrib.name.lower() for kw in keywords):
            evidence.append(f"- **Contributor:** {contrib.name} ({contrib.commit_count} commits)")

    # Build response
    lines = [
        f"# Analysis: {question}",
        "",
        f"> Based on heuristic analysis of `{profile.name}`. "
        "This is evidence-based, not LLM-generated.",
        "",
    ]

    if evidence:
        lines.append("## Evidence Found")
        lines.append("")
        lines.extend(evidence)
    else:
        lines.append("## No Direct Evidence Found")
        lines.append("")
        lines.append(
            "The heuristic analyzer could not find direct evidence for this question. "
            "Consider asking about specific technologies, patterns, or structural decisions."
        )
        lines.append("")
        lines.append(
            "**Available topics:** dependencies, framework choice, directory layout, "
            "testing strategy, CI/CD, naming conventions, architecture patterns."
        )

    lines.append("")
    lines.append("## Context")
    lines.append("")
    lines.append(f"- **Project:** {profile.name}")
    lines.append(f"- **Language:** {profile.code_structure.primary_language}")
    if profile.dependencies.framework:
        lines.append(f"- **Framework:** {profile.dependencies.framework}")
    lines.append(f"- **Commits analyzed:** {profile.git_history.total_commits}")

    return "\n".join(lines)


@mcp.tool()
def generate_claude_md(path: str, style: str = "standard") -> str:
    """Generate a CLAUDE.md file for a repository.

    Args:
        path: Path to the repository root.
        style: "standard" (full) or "minimal" (compact).

    Returns:
        CLAUDE.md content as markdown string.
    """
    profile = analyze_repo(path, include_git_history=True, max_files=500)
    docs = generate_docs(profile, docs=["claude-md"], style=style)
    return docs["CLAUDE.md"]


@mcp.tool()
def map_tribal_knowledge(path: str) -> dict:
    """Map undocumented conventions, knowledge silos, and risk areas.

    Args:
        path: Path to the repository root.

    Returns:
        Dict with conventions, knowledge_silos, risk_areas, recommendations.
    """
    profile = analyze_repo(path, include_git_history=True, max_files=500)

    conventions = []
    for conv in profile.patterns.naming_conventions:
        conventions.append(
            {
                "name": conv.name,
                "pattern": conv.pattern,
                "confidence": conv.confidence,
                "examples": conv.examples,
            }
        )
    for pattern in profile.patterns.architecture_patterns:
        conventions.append(
            {
                "name": f"Architecture: {pattern}",
                "pattern": pattern,
                "confidence": 0.8,
                "examples": [],
            }
        )

    # Knowledge silos: files with only 1 contributor
    knowledge_silos = []
    for hot_file in profile.git_history.hot_files:
        if hot_file.unique_contributors == 1:
            knowledge_silos.append(
                {
                    "file": hot_file.path,
                    "changes": hot_file.change_count,
                    "risk": "Single contributor — knowledge silo",
                }
            )

    # Risk areas
    risk_areas = []
    if profile.git_history.bus_factor <= 1:
        risk_areas.append(
            {
                "type": "bus_factor",
                "severity": "critical",
                "description": f"Bus factor is {profile.git_history.bus_factor}. "
                "Single point of failure for project knowledge.",
            }
        )
    if profile.patterns.type_hint_ratio < 0.3:
        risk_areas.append(
            {
                "type": "type_safety",
                "severity": "medium",
                "description": (
                    f"Only {profile.patterns.type_hint_ratio:.0%} of functions have type hints."
                ),
            }
        )
    if profile.patterns.docstring_ratio < 0.2:
        risk_areas.append(
            {
                "type": "documentation",
                "severity": "medium",
                "description": (
                    f"Only {profile.patterns.docstring_ratio:.0%} of functions have docstrings."
                ),
            }
        )
    if not profile.code_structure.has_ci:
        risk_areas.append(
            {
                "type": "ci_cd",
                "severity": "high",
                "description": "No CI/CD pipeline detected.",
            }
        )
    if not profile.code_structure.has_tests:
        risk_areas.append(
            {
                "type": "testing",
                "severity": "high",
                "description": "No test directory detected.",
            }
        )

    # Recommendations
    recommendations = []
    if knowledge_silos:
        recommendations.append(
            "Spread knowledge: assign code reviews across team members for silo files."
        )
    if profile.git_history.bus_factor <= 1:
        recommendations.append("Pair programming or mentoring to increase bus factor.")
    if profile.patterns.type_hint_ratio < 0.5:
        recommendations.append("Add type hints incrementally, starting with public APIs.")
    if profile.patterns.docstring_ratio < 0.3:
        recommendations.append("Add docstrings to public functions and classes.")
    if not profile.code_structure.has_ci:
        recommendations.append("Set up CI/CD pipeline for automated testing.")

    return {
        "project": profile.name,
        "conventions": conventions,
        "knowledge_silos": knowledge_silos,
        "risk_areas": risk_areas,
        "recommendations": recommendations,
    }


def _extract_keywords(question: str) -> list[str]:
    """Extract meaningful keywords from a question."""
    stop_words = {
        "why",
        "what",
        "how",
        "is",
        "are",
        "was",
        "were",
        "do",
        "does",
        "did",
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "they",
        "them",
        "use",
        "used",
        "using",
        "project",
        "repo",
        "codebase",
    }
    words = re.findall(r"[a-zA-Z0-9_-]+", question.lower())
    return [w for w in words if w not in stop_words and len(w) > 1]


if __name__ == "__main__":
    mcp.run()
