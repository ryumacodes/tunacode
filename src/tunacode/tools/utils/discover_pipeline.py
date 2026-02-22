"""Synchronous discovery pipeline and helper functions for code mapping."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from tunacode.tools.ignore import IgnoreManager, get_ignore_manager
from tunacode.tools.utils.discover_terms import (
    ALL_KEYWORDS,
    CONCEPT_EXPANSIONS,
    NOISE_WORDS,
    SOURCE_EXTENSIONS,
)
from tunacode.tools.utils.discover_types import (
    MAX_EXCERPT_LINES,
    MAX_GLOB_CANDIDATES,
    MAX_IMPORTS_PER_FILE,
    MAX_PREVIEW_LINES,
    MAX_REPORT_FILES,
    MAX_SYMBOLS_PER_FILE,
    ConceptCluster,
    DiscoveryReport,
    FileEntry,
    Relevance,
)


def _extract_search_terms(query: str) -> dict[str, list[str]]:
    """Extract exact identifiers, filename terms, and content terms from natural language."""
    words = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", query.lower()))

    exact: list[str] = re.findall(r"[A-Z][a-zA-Z0-9]+(?:[A-Z][a-zA-Z0-9]+)+", query)
    exact += re.findall(r"[a-z]+(?:_[a-z]+)+", query)
    exact += re.findall(r"[\w]+\.[\w]+", query)

    filename_terms: list[str] = []
    content_terms: list[str] = []

    for word in words:
        if word in NOISE_WORDS:
            continue

        matched = False
        for concept, expansions in CONCEPT_EXPANSIONS.items():
            if word == concept or (
                len(word) >= 4 and (word.startswith(concept) or concept.startswith(word))
            ):
                filename_terms.extend(expansions[:4])
                content_terms.extend(expansions)
                matched = True
                break

        if not matched:
            filename_terms.append(word)
            content_terms.append(word)

    filename_terms = [term for term in filename_terms if term not in NOISE_WORDS]
    content_terms = [term for term in content_terms if term not in NOISE_WORDS]

    return {
        "exact": list(dict.fromkeys(exact)),
        "filename": list(dict.fromkeys(filename_terms)),
        "content": list(dict.fromkeys(content_terms)),
    }


def _detect_dominant_extensions(
    project_root: Path,
    sample_limit: int = 300,
    walk_limit: int = 5000,
) -> list[str]:
    """Sample the project to find the most common source extensions.

    Caps both source file matches (sample_limit) and total paths walked
    (walk_limit) to avoid unbounded iteration on large repos.
    """
    ext_counts: dict[str, int] = {}
    source_count = 0

    for walked, path in enumerate(project_root.rglob("*")):
        if walked >= walk_limit or source_count >= sample_limit:
            break

        if path.is_file() and path.suffix in SOURCE_EXTENSIONS:
            ext_counts[path.suffix] = ext_counts.get(path.suffix, 0) + 1
            source_count += 1

    sorted_exts = sorted(ext_counts.items(), key=lambda item: -item[1])
    return [ext for ext, count in sorted_exts if count > 2][:6]


def _generate_glob_patterns(terms: dict[str, list[str]], extensions: list[str]) -> list[str]:
    """Generate 3x+ patterns per filename term: filename, directory, per-extension."""
    patterns: list[str] = []

    for term in terms["filename"]:
        patterns.append(f"**/*{term}*")
        patterns.append(f"**/{term}*/**")
        patterns.append(f"**/*{term}*/**")
        for ext in extensions:
            patterns.append(f"**/*{term}*{ext}")

    return list(dict.fromkeys(patterns))


def _extract_terms_from_patterns(patterns: list[str]) -> set[str]:
    """Extract core search terms from glob patterns for single-walk matching."""
    terms: set[str] = set()
    for pattern in patterns:
        core = pattern.replace("**/", "").replace("/**", "").replace("*", "")
        for ext in SOURCE_EXTENSIONS:
            if core.endswith(ext):
                core = core[: -len(ext)]
                break
        if core:
            terms.add(core.lower())

    return terms


def _collect_candidates(
    patterns: list[str],
    root: Path,
    ignore_manager: IgnoreManager,
    max_candidates: int = MAX_GLOB_CANDIDATES,
) -> list[Path]:
    """Walk the tree once, test each source file against all pattern terms."""
    terms = _extract_terms_from_patterns(patterns)
    candidates: dict[str, Path] = {}

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_EXTENSIONS:
            continue

        if ignore_manager.should_ignore(path):
            continue

        path_lower = str(path).lower()
        if not any(term in path_lower for term in terms):
            continue

        key = str(path.resolve())
        if key not in candidates:
            candidates[key] = path

        if len(candidates) >= max_candidates:
            break

    result = sorted(candidates.values(), key=lambda candidate: len(candidate.parts))
    return result[:max_candidates]


@dataclass
class _Prospect:
    path: Path
    keep: bool
    relevance: Relevance
    role: str
    key_symbols: list[str]
    imports: list[str]
    excerpt: str
    line_count: int
    score: float = 0.0


def _evaluate_prospect(
    path: Path,
    terms: dict[str, list[str]],
    max_preview_lines: int = MAX_PREVIEW_LINES,
) -> _Prospect:
    """Read first N lines, score against search terms, decide keep/skip."""
    try:
        text = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return _empty_prospect(path)

    all_lines = text.splitlines()
    line_count = len(all_lines)
    preview = "\n".join(all_lines[:max_preview_lines])
    preview_lower = preview.lower()

    exact_hits = sum(1 for term in terms["exact"] if term in preview)
    content_hits = sum(1 for term in terms["content"] if term.lower() in preview_lower)
    path_lower = str(path).lower()
    filename_hits = sum(1 for term in terms["filename"] if term in path_lower)

    score = (exact_hits * 3.0) + (content_hits * 1.0) + (filename_hits * 2.0)

    if exact_hits >= 1 or content_hits >= 3 or (filename_hits >= 2 and content_hits >= 1):
        relevance = Relevance.HIGH
    elif content_hits >= 2 or (filename_hits >= 1 and content_hits >= 1):
        relevance = Relevance.MEDIUM
    else:
        return _empty_prospect(path)

    symbols = _extract_symbols(preview)
    imports = _extract_imports(preview)
    role = _infer_role(path, symbols)
    excerpt = _build_excerpt(all_lines[:max_preview_lines], terms, max_lines=MAX_EXCERPT_LINES)

    return _Prospect(
        path=path,
        keep=True,
        relevance=relevance,
        role=role,
        key_symbols=symbols[:MAX_SYMBOLS_PER_FILE],
        imports=imports[:MAX_IMPORTS_PER_FILE],
        excerpt=excerpt,
        line_count=line_count,
        score=score,
    )


def _empty_prospect(path: Path) -> _Prospect:
    return _Prospect(
        path=path,
        keep=False,
        relevance=Relevance.MEDIUM,
        role="",
        key_symbols=[],
        imports=[],
        excerpt="",
        line_count=0,
    )


def _extract_symbols(text: str) -> list[str]:
    """Extract function/class/struct names, filtering out language keywords."""
    symbols: list[str] = []

    symbols.extend(re.findall(r"(?:def|class)\s+([a-zA-Z_]\w+)", text))
    symbols.extend(re.findall(r"function\s+([a-zA-Z_]\w+)", text))
    symbols.extend(re.findall(r"(?:export\s+)?class\s+([a-zA-Z_]\w+)", text))

    for match in re.finditer(r"func\s+(?:\([^)]+\)\s+)?([a-zA-Z_]\w+)", text):
        symbols.append(match.group(1))

    symbols.extend(re.findall(r"(?:pub\s+)?(?:fn|struct|enum|trait)\s+([a-zA-Z_]\w+)", text))

    seen: set[str] = set()
    filtered: list[str] = []
    for symbol in symbols:
        if symbol not in seen and symbol not in ALL_KEYWORDS:
            seen.add(symbol)
            filtered.append(symbol)

    return filtered


def _extract_imports(text: str) -> list[str]:
    """Extract import paths from source code."""
    imports: list[str] = []
    imports.extend(re.findall(r"from\s+([\w.]+)\s+import", text))
    imports.extend(re.findall(r"^import\s+([\w.]+)", text, re.MULTILINE))
    imports.extend(re.findall(r'from\s+["\']([^"\']+)["\']', text))
    imports.extend(re.findall(r'require\(["\']([^"\']+)["\']\)', text))
    return list(dict.fromkeys(imports))


def _infer_role(path: Path, symbols: list[str]) -> str:
    """Build a short role description from path and top symbols."""
    parent = path.parent.name if path.parent.name != "." else ""
    name = path.stem
    base = f"{parent}/{name}" if parent else name
    if symbols:
        return f"{base} ({', '.join(symbols[:2])})"
    return base


def _build_excerpt(
    lines: list[str],
    terms: dict[str, list[str]],
    max_lines: int = MAX_EXCERPT_LINES,
) -> str:
    """Pick the most relevant lines as a compact excerpt."""
    all_terms = [term.lower() for term in terms["exact"] + terms["content"]]
    scored: list[tuple[float, int, str]] = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue

        line_lower = stripped.lower()
        score = float(sum(1 for term in all_terms if term in line_lower))

        if re.match(r"\s*(def |class |function |fn |struct |export )", line):
            score += 0.5

        if score > 0:
            scored.append((score, index, stripped))

    scored.sort(key=lambda item: -item[0])
    top = scored[:max_lines]
    top.sort(key=lambda item: item[1])
    return " | ".join(item[2][:120] for item in top)


def _cluster_prospects(
    prospects: list[_Prospect],
) -> tuple[list[ConceptCluster], list[str]]:
    """Group kept prospects by directory.

    Returns (clusters, overflow_dirs) where overflow_dirs lists directories
    whose files were trimmed to stay within MAX_REPORT_FILES.
    """
    kept = [prospect for prospect in prospects if prospect.keep]
    kept.sort(key=lambda prospect: -prospect.score)

    dir_groups: dict[str, list[_Prospect]] = {}
    for prospect in kept:
        key = str(prospect.path.parent)
        dir_groups.setdefault(key, []).append(prospect)

    clusters: list[ConceptCluster] = []
    for dir_path, group in dir_groups.items():
        name = Path(dir_path).name or "root"
        high = sum(1 for prospect in group if prospect.relevance == Relevance.HIGH)
        files = [
            FileEntry(
                path=str(prospect.path),
                relevance=prospect.relevance,
                role=prospect.role,
                key_symbols=prospect.key_symbols,
                imports_from=prospect.imports,
                line_count=prospect.line_count,
                excerpt=prospect.excerpt,
            )
            for prospect in sorted(group, key=lambda item: -item.score)
        ]
        clusters.append(
            ConceptCluster(
                name=name,
                description=f"{len(group)} files ({high} high relevance)",
                files=files,
            )
        )

    clusters.sort(
        key=lambda cluster: -sum(
            1 for file_entry in cluster.files if file_entry.relevance == Relevance.HIGH
        )
    )

    total_files = 0
    trimmed_clusters: list[ConceptCluster] = []
    overflow_dirs: list[str] = []

    for cluster in clusters:
        remaining = MAX_REPORT_FILES - total_files
        if remaining <= 0:
            overflow_dirs.append(cluster.name)
            continue

        if len(cluster.files) <= remaining:
            trimmed_clusters.append(cluster)
            total_files += len(cluster.files)
            continue

        overflow_count = len(cluster.files) - remaining
        trimmed = ConceptCluster(
            name=cluster.name,
            description=f"{remaining} of {len(cluster.files)} files shown",
            files=cluster.files[:remaining],
        )
        trimmed_clusters.append(trimmed)
        total_files += remaining
        overflow_dirs.append(f"{cluster.name} (+{overflow_count})")

    return trimmed_clusters, overflow_dirs


def _build_relevant_tree(prospects: list[_Prospect], root: Path) -> str:
    """Build a file tree showing only kept prospects."""
    kept = [prospect for prospect in prospects if prospect.keep]
    if not kept:
        return ""

    resolved_root = root.resolve()
    dirs: set[str] = set()
    file_relevance: dict[str, Relevance] = {}

    for prospect in kept:
        try:
            rel = str(prospect.path.resolve().relative_to(resolved_root))
        except ValueError:
            continue

        file_relevance[rel] = prospect.relevance
        for parent in Path(rel).parents:
            parent_str = str(parent)
            if parent_str != ".":
                dirs.add(parent_str)

    all_paths = sorted(dirs | set(file_relevance.keys()))
    lines: list[str] = []
    for path_str in all_paths:
        depth = path_str.count(os.sep)
        name = Path(path_str).name
        prefix = "  " * depth
        if path_str in file_relevance:
            marker = "★" if file_relevance[path_str] == Relevance.HIGH else "◆"
            lines.append(f"{prefix}{marker} {name}")
        else:
            lines.append(f"{prefix}{name}/")

    return "\n".join(lines)


def _discover_sync(query: str, project_root: str) -> DiscoveryReport:
    """Synchronous discovery pipeline. Offloaded to a thread by the async wrapper."""
    root = Path(project_root).resolve()
    ignore_manager = get_ignore_manager(root)

    terms = _extract_search_terms(query)
    extensions = _detect_dominant_extensions(root)
    patterns = _generate_glob_patterns(terms, extensions)
    candidates = _collect_candidates(patterns, root, ignore_manager)

    prospects = [_evaluate_prospect(path, terms) for path in candidates]
    kept = [prospect for prospect in prospects if prospect.keep]

    clusters, overflow_dirs = _cluster_prospects(prospects)
    tree = _build_relevant_tree(prospects, root)

    high = sum(1 for prospect in kept if prospect.relevance == Relevance.HIGH)
    medium = sum(1 for prospect in kept if prospect.relevance == Relevance.MEDIUM)

    cluster_count = len(clusters)
    summary = (
        f"Found {len(kept)} relevant files ({high} high, {medium} medium) in {cluster_count} areas."
    )
    if clusters:
        summary += f" Key: {', '.join(cluster.name for cluster in clusters[:3])}."

    return DiscoveryReport(
        query=query,
        summary=summary,
        clusters=clusters,
        file_tree=tree,
        total_files_scanned=len(candidates),
        total_candidates=len(kept),
        overflow_dirs=overflow_dirs,
    )
