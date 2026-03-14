"""Data structures and report formatting for discover tool output."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

MAX_REPORT_FILES = 20
MAX_PREVIEW_LINES = 200
MAX_GLOB_CANDIDATES = 150
MAX_EXCERPT_LINES = 3
MAX_SYMBOLS_PER_FILE = 8
MAX_IMPORTS_PER_FILE = 8


class Relevance(Enum):
    HIGH = "high"
    MEDIUM = "medium"


@dataclass
class FileEntry:
    """A single discovered file with its role in the codebase."""

    path: str
    relevance: Relevance
    role: str
    key_symbols: list[str]
    imports_from: list[str]
    line_count: int = 0
    excerpt: str = ""


@dataclass
class ConceptCluster:
    """Group of files that together implement a concept."""

    name: str
    description: str
    files: list[FileEntry] = field(default_factory=list)


@dataclass
class DiscoveryReport:
    """Compact typed report for model consumption."""

    query: str
    summary: str
    clusters: list[ConceptCluster] = field(default_factory=list)
    file_tree: str = ""
    total_files_scanned: int = 0
    total_candidates: int = 0
    overflow_dirs: list[str] = field(default_factory=list)

    def to_context(self) -> str:
        """Serialize to compact string for model consumption."""
        lines: list[str] = []
        lines.append(f"# Discovery: {self.query}")
        lines.append(self.summary)
        lines.append(f"({self.total_files_scanned} scanned → {self.total_candidates} relevant)")
        lines.append(f"scanned: {self.total_files_scanned} | relevant: {self.total_candidates}\n")

        if self.file_tree:
            lines.append("```")
            lines.append(self.file_tree)
            lines.append("```\n")

        for cluster in self.clusters:
            lines.append(f"## {cluster.name}")
            lines.append(f"{cluster.description}\n")
            for file_entry in cluster.files:
                marker = "★" if file_entry.relevance == Relevance.HIGH else "◆"
                lines.append(
                    f"  {marker} `{file_entry.path}` — {file_entry.role} ({file_entry.line_count}L)"
                )
                if file_entry.key_symbols:
                    lines.append(
                        f"    defines: {', '.join(file_entry.key_symbols[:MAX_SYMBOLS_PER_FILE])}"
                    )
                if file_entry.imports_from:
                    lines.append(
                        f"    imports: {', '.join(file_entry.imports_from[:MAX_IMPORTS_PER_FILE])}"
                    )
                if file_entry.excerpt:
                    lines.append(f"    context: {file_entry.excerpt}")
            lines.append("")

        if self.overflow_dirs:
            lines.append(f"(+{len(self.overflow_dirs)} more in: {', '.join(self.overflow_dirs)})")
            lines.append("")

        return "\n".join(lines)
