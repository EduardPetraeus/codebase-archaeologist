"""Data models — contracts between analyzers and generators."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Contributor:
    name: str
    email: str
    commit_count: int = 0
    files_touched: list[str] = field(default_factory=list)
    first_commit_date: str = ""
    last_commit_date: str = ""


@dataclass
class HotFile:
    path: str
    change_count: int
    unique_contributors: int
    last_modified: str = ""


@dataclass
class GitHistoryResult:
    total_commits: int = 0
    contributors: list[Contributor] = field(default_factory=list)
    hot_files: list[HotFile] = field(default_factory=list)
    bus_factor: int = 0
    conventional_commits_ratio: float = 0.0
    commit_frequency_per_week: float = 0.0
    first_commit_date: str = ""
    last_commit_date: str = ""
    active_branches: list[str] = field(default_factory=list)


@dataclass
class ConfigFile:
    path: str
    type: str  # e.g. "pyproject.toml", "package.json", "Makefile"


@dataclass
class EntryPoint:
    path: str
    type: str  # e.g. "cli", "main", "server", "api"
    description: str = ""


@dataclass
class CodeStructureResult:
    primary_language: str = "unknown"
    languages: dict[str, int] = field(default_factory=dict)  # language -> file count
    total_files: int = 0
    total_lines: int = 0
    src_layout: bool = False  # has src/ directory
    has_tests: bool = False
    test_directory: str = ""
    has_ci: bool = False
    ci_system: str = ""
    config_files: list[ConfigFile] = field(default_factory=list)
    entry_points: list[EntryPoint] = field(default_factory=list)
    directory_tree: dict[str, list[str]] = field(default_factory=dict)  # dir -> files


@dataclass
class Convention:
    name: str
    pattern: str
    confidence: float  # 0.0 - 1.0
    examples: list[str] = field(default_factory=list)


@dataclass
class PatternResult:
    naming_conventions: list[Convention] = field(default_factory=list)
    architecture_patterns: list[str] = field(default_factory=list)  # e.g. "MVC", "layered"
    test_patterns: list[str] = field(default_factory=list)  # e.g. "AAA", "pytest fixtures"
    type_hint_ratio: float = 0.0
    docstring_ratio: float = 0.0
    avg_function_length: float = 0.0
    has_type_checking: bool = False


@dataclass
class Dependency:
    name: str
    version_constraint: str = ""
    category: str = ""  # e.g. "web", "testing", "database", "cli"


@dataclass
class DependencyResult:
    package_manager: str = ""  # e.g. "pip", "npm", "cargo"
    framework: str = ""  # e.g. "FastAPI", "Django", "React"
    framework_version: str = ""
    dependencies: list[Dependency] = field(default_factory=list)
    dev_dependencies: list[Dependency] = field(default_factory=list)
    python_version: str = ""
    tech_categories: dict[str, list[str]] = field(default_factory=dict)  # category -> dep names


@dataclass
class CodebaseProfile:
    """Aggregated result from all analyzers — input to generators."""

    path: Path = field(default_factory=Path)
    name: str = ""
    git_history: GitHistoryResult = field(default_factory=GitHistoryResult)
    code_structure: CodeStructureResult = field(default_factory=CodeStructureResult)
    patterns: PatternResult = field(default_factory=PatternResult)
    dependencies: DependencyResult = field(default_factory=DependencyResult)

    def to_dict(self) -> dict:
        """Convert to a serializable dict for MCP tool responses."""
        import dataclasses

        def _convert(obj):
            if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
                d = {k: _convert(v) for k, v in dataclasses.asdict(obj).items()}
                # Redact absolute path — only expose repo name
                if "path" in d and isinstance(d["path"], str) and "/" in d["path"]:
                    d["path"] = d["path"].rsplit("/", 1)[-1]
                return d
            if isinstance(obj, Path):
                return str(obj)
            return obj

        return _convert(self)
