"""Code discovery tool entrypoint and compatibility re-exports."""

from __future__ import annotations

import asyncio

from tunacode.tools.decorators import base_tool
from tunacode.tools.utils.discover_pipeline import (
    _build_excerpt,
    _build_relevant_tree,
    _cluster_prospects,
    _collect_candidates,
    _detect_dominant_extensions,
    _discover_sync,
    _empty_prospect,
    _evaluate_prospect,
    _extract_imports,
    _extract_search_terms,
    _extract_symbols,
    _generate_glob_patterns,
    _infer_role,
    _Prospect,
)
from tunacode.tools.utils.discover_types import (
    MAX_REPORT_FILES,
    ConceptCluster,
    DiscoveryReport,
    FileEntry,
    Relevance,
)


@base_tool
async def discover(
    query: str,
    directory: str = ".",
) -> str:
    """Find and map code related to a concept, feature, or module.

    Describe what you're looking for in natural language. Returns a structured
    report of relevant files, their roles, key symbols, and relationships.
    Use INSTEAD of manually chaining glob, grep, and read.

    Args:
        query: What to find, e.g. "where is auth handled",
               "database schema and migrations", "tool registration and execution".
        directory: Project root to search from (default: current directory).

    Returns:
        Compact discovery report with file map, clusters, symbols, and excerpts.
    """
    report = await asyncio.to_thread(_discover_sync, query, directory)
    return report.to_context()


__all__ = [
    "MAX_REPORT_FILES",
    "ConceptCluster",
    "DiscoveryReport",
    "FileEntry",
    "Relevance",
    "_Prospect",
    "_build_excerpt",
    "_build_relevant_tree",
    "_cluster_prospects",
    "_collect_candidates",
    "_detect_dominant_extensions",
    "_discover_sync",
    "_empty_prospect",
    "_evaluate_prospect",
    "_extract_imports",
    "_extract_search_terms",
    "_extract_symbols",
    "_generate_glob_patterns",
    "_infer_role",
    "discover",
]
