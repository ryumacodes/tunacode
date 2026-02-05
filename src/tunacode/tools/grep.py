"""
Parallel grep tool for TunaCode - Enhanced content search with parallel processing.

This tool provides sophisticated grep-like functionality with:
- Parallel file searching across multiple directories
- Multiple search strategies (literal, regex, fuzzy)
- Smart result ranking and deduplication
- Context-aware output formatting
- Timeout handling for overly broad patterns (3 second deadline for first match)

CLAUDE_ANCHOR[grep-module]: Fast parallel file search with 3-second deadline
"""

import asyncio
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from tunacode.configuration.defaults import DEFAULT_USER_CONFIG
from tunacode.exceptions import TooBroadPatternError, ToolExecutionError, ToolRetryError

from tunacode.tools.decorators import base_tool
from tunacode.tools.grep_components import (
    FileFilter,
    PatternMatcher,
    SearchConfig,
    SearchResult,
)
from tunacode.tools.grep_components.result_formatter import ResultFormatter
from tunacode.tools.utils.ripgrep import RipgrepExecutor
from tunacode.tools.utils.ripgrep import metrics as ripgrep_metrics

SMART_PYTHON_THRESHOLD = 50
SMART_RIPGREP_THRESHOLD = 1000


def _select_search_strategy(search_type: str, candidate_count: int) -> str:
    """Select concrete search strategy based on candidate count."""
    if search_type != "smart":
        return search_type
    if candidate_count <= SMART_PYTHON_THRESHOLD:
        return "python"
    if candidate_count <= SMART_RIPGREP_THRESHOLD:
        return "ripgrep"
    return "hybrid"


def _format_search_output(
    results: list[SearchResult],
    pattern: str,
    config: SearchConfig,
    output_mode: str,
    search_type: str,
    original_search_type: str,
    candidate_count: int,
    return_format: str,
    formatter: ResultFormatter,
) -> str | list[str]:
    """Format search results for output."""
    formatted = formatter.format_results(results, pattern, config, output_mode=output_mode)

    if return_format == "list":
        return list({r.file_path for r in results})

    if formatted.startswith("Found"):
        lines = formatted.split("\n")
        lines[1] = f"Strategy: {search_type} | Candidates: {candidate_count} files | " + lines[1]
        return "\n".join(lines)

    strategy_info = (
        f"Strategy: {search_type} (was {original_search_type}), "
        f"Files: {candidate_count}/{MAX_CANDIDATE_FILES}"
    )
    return f"{formatted}\n\n{strategy_info}"


MAX_CANDIDATE_FILES = 5000


async def _check_deadline(
    deadline: float,
    first_match_event: asyncio.Event,
    search_tasks: list[asyncio.Task[list[SearchResult]]],
    pattern: str,
) -> None:
    """Monitor for first match deadline, cancelling tasks if exceeded."""
    await asyncio.sleep(deadline)
    if not first_match_event.is_set():
        for task in search_tasks:
            if not task.done():
                task.cancel()
        raise TooBroadPatternError(pattern, deadline)


def _flatten_search_results(
    all_results: list[list[SearchResult] | BaseException],
    max_results: int,
) -> list[SearchResult]:
    """Flatten gathered search results, filtering out exceptions."""
    results: list[SearchResult] = []
    for file_results in all_results:
        if isinstance(file_results, list):
            results.extend(file_results)
    results.sort(key=lambda r: r.relevance_score, reverse=True)
    return results[:max_results]


class ParallelGrep:
    """Advanced parallel grep tool with multiple search strategies."""

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=8)
        self._file_filter = FileFilter()
        self._pattern_matcher = PatternMatcher()
        self._result_formatter = ResultFormatter()
        self._ripgrep_executor = RipgrepExecutor()
        self._config = self._load_ripgrep_config()

    def _load_ripgrep_config(self) -> dict[str, Any]:
        """Load ripgrep configuration from defaults."""
        return DEFAULT_USER_CONFIG["settings"]["ripgrep"]

    async def _run_search_strategy(
        self,
        search_type: str,
        pattern: str,
        candidates: list[Path],
        config: SearchConfig,
    ) -> list[SearchResult]:
        """Execute the selected search strategy."""
        if search_type == "ripgrep":
            results = await self._ripgrep_search_filtered(pattern, candidates, config)
            if not results:
                results = await self._python_search_filtered(pattern, candidates, config)
            return results
        if search_type == "python":
            return await self._python_search_filtered(pattern, candidates, config)
        if search_type == "hybrid":
            return await self._hybrid_search_filtered(pattern, candidates, config)
        raise ToolExecutionError(tool_name="grep", message=f"Unknown search type: {search_type}")

    async def execute(
        self,
        pattern: str,
        directory: str = ".",
        case_sensitive: bool = False,
        use_regex: bool = False,
        include_files: str | None = None,
        exclude_files: str | None = None,
        max_results: int = 50,
        context_lines: int = 2,
        search_type: str = "smart",  # smart, ripgrep, python, hybrid
        return_format: str = "string",  # "string" (default) or "list" (legacy)
        output_mode: str = "content",  # content, files_with_matches, count, json
    ) -> str | list[str]:
        """
        Execute parallel grep search with fast-glob prefiltering and multiple strategies.

        Args:
            pattern: Search pattern (literal text or regex)
            directory: Directory to search (default: current)
            case_sensitive: Whether search is case sensitive
            use_regex: Whether pattern is a regular expression
            include_files: File patterns to include (e.g., "*.py", "*.{js,ts}")
            exclude_files: File patterns to exclude (e.g., "*.pyc", "node_modules/*")
            max_results: Maximum number of results to return
            context_lines: Number of context lines before/after matches
            search_type: Search strategy to use

        Returns:
            Formatted search results
        """
        try:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                raise ToolRetryError(f"Directory not found: {directory}. Check the path.")
            if not dir_path.is_dir():
                raise ToolRetryError(f"Not a directory: {directory}. Provide a directory path.")

            include_pattern = include_files or "*"
            candidates = await asyncio.get_running_loop().run_in_executor(
                self._executor,
                self._file_filter.fast_glob,
                Path(directory),
                include_pattern,
                exclude_files,
            )

            if not candidates:
                if return_format == "list":
                    return []
                return f"No files found matching pattern: {include_pattern}"

            original_search_type = search_type
            resolved_strategy = _select_search_strategy(search_type, len(candidates))

            include_patterns = (
                self._file_filter.parse_patterns(include_files) if include_files else ["*"]
            )
            exclude_patterns = (
                self._file_filter.parse_patterns(exclude_files) if exclude_files else []
            )
            config = SearchConfig(
                case_sensitive=case_sensitive,
                use_regex=use_regex,
                max_results=max_results,
                context_lines=context_lines,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            )

            results = await self._run_search_strategy(
                resolved_strategy,
                pattern,
                candidates,
                config,
            )

            return _format_search_output(
                results,
                pattern,
                config,
                output_mode,
                resolved_strategy,
                original_search_type,
                len(candidates),
                return_format,
                self._result_formatter,
            )

        except (TooBroadPatternError, ToolRetryError):
            raise
        except Exception as err:
            raise ToolExecutionError(
                tool_name="grep", message=f"Grep search failed: {err}"
            ) from err

    # ====== SEARCH METHODS ======

    async def _ripgrep_search_filtered(
        self, pattern: str, candidates: list[Path], config: SearchConfig
    ) -> list[SearchResult]:
        """
        Run ripgrep on pre-filtered file list using the enhanced RipgrepExecutor.
        """
        start_time = time.time()
        results: list[SearchResult] = []

        timeout_setting = self._config.get("timeout", 10)
        timeout = min(timeout_setting, config.timeout_seconds)

        if self._ripgrep_executor._use_python_fallback:
            return []

        try:
            # Use the enhanced executor with support for context lines
            # Note: Currently searching all files, not using candidates
            # This is a limitation that should be addressed in future enhancement
            search_results = await self._ripgrep_executor.search(
                pattern=pattern,
                path=".",  # Search in current directory
                timeout=timeout,
                max_matches=config.max_results,
                case_insensitive=not config.case_sensitive,
                context_before=config.context_lines,
                context_after=config.context_lines,
            )

            # Ripgrep doesn't provide timing info for first match, so we rely on
            # the overall timeout mechanism instead of first_match_deadline

            # Parse results
            for result_line in search_results:
                # Parse ripgrep output format "file:line:content"
                parts = result_line.split(":", 2)
                if len(parts) < 3:
                    continue

                # Filter to only include results from candidates
                file_path = Path(parts[0])
                if file_path not in candidates:
                    continue

                try:
                    line_content = parts[2]
                    search_result = SearchResult(
                        file_path=parts[0],
                        line_number=int(parts[1]),
                        line_content=line_content,
                        match_start=0,
                        match_end=len(line_content),
                        context_before=[],
                        context_after=[],
                        relevance_score=1.0,
                    )
                    results.append(search_result)

                    # Stop if we have enough results
                    if config.max_results and len(results) >= config.max_results:
                        break
                except (ValueError, IndexError):
                    continue

        except TooBroadPatternError:
            raise
        except Exception:
            # Return empty to trigger fallback
            return []

        if self._config.get("enable_metrics", False):
            total_time = time.time() - start_time
            ripgrep_metrics.record_search(
                duration=total_time, used_fallback=self._ripgrep_executor._use_python_fallback
            )

        return results

    async def _python_search_filtered(
        self, pattern: str, candidates: list[Path], config: SearchConfig
    ) -> list[SearchResult]:
        """
        Run Python parallel search on pre-filtered candidates with first match deadline.
        """
        if config.use_regex:
            flags = 0 if config.case_sensitive else re.IGNORECASE
            regex_pattern: re.Pattern[str] | None = re.compile(pattern, flags)
        else:
            regex_pattern = None

        first_match_event = asyncio.Event()
        search_tasks = [
            asyncio.create_task(
                self._monitored_file_search(fp, pattern, regex_pattern, config, first_match_event)
            )
            for fp in candidates
        ]
        deadline_task = asyncio.create_task(
            _check_deadline(config.first_match_deadline, first_match_event, search_tasks, pattern)
        )

        try:
            all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            deadline_task.cancel()
            return _flatten_search_results(all_results, config.max_results)
        except asyncio.CancelledError:
            if deadline_task.done():
                try:
                    await deadline_task
                except TooBroadPatternError:
                    raise
            return []

    async def _monitored_file_search(
        self,
        file_path: Path,
        pattern: str,
        regex_pattern: re.Pattern[str] | None,
        config: SearchConfig,
        first_match_event: asyncio.Event,
    ) -> list[SearchResult]:
        """Search a file and signal when first match is found."""
        try:
            file_results = await self._search_file(file_path, pattern, regex_pattern, config)
            if file_results and not first_match_event.is_set():
                first_match_event.set()
            return file_results
        except Exception:
            return []

    async def _hybrid_search_filtered(
        self, pattern: str, candidates: list[Path], config: SearchConfig
    ) -> list[SearchResult]:
        """
        Hybrid approach using multiple search methods concurrently on pre-filtered candidates.
        """

        # Run multiple search strategies in parallel
        tasks = [
            self._ripgrep_search_filtered(pattern, candidates, config),
            self._python_search_filtered(pattern, candidates, config),
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Check if any task raised TooBroadPatternError
        too_broad_errors = [r for r in results_list if isinstance(r, TooBroadPatternError)]
        if too_broad_errors:
            # If both strategies timed out, raise the error
            valid_results = [r for r in results_list if isinstance(r, list)]
            if not valid_results:
                raise too_broad_errors[0]

        # Merge and deduplicate results
        all_results = []
        for results in results_list:
            if isinstance(results, list):
                all_results.extend(results)

        # Deduplicate by file path and line number
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result.file_path, result.line_number)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # Sort and limit
        unique_results.sort(key=lambda r: r.relevance_score, reverse=True)
        return unique_results[: config.max_results]

    async def _search_file(
        self,
        file_path: Path,
        pattern: str,
        regex_pattern: re.Pattern | None,
        config: SearchConfig,
    ) -> list[SearchResult]:
        """Search a single file for the pattern."""

        def search_file_sync() -> list[SearchResult]:
            return self._pattern_matcher.search_file(file_path, pattern, regex_pattern, config)

        return await asyncio.get_running_loop().run_in_executor(self._executor, search_file_sync)


@base_tool
async def grep(
    pattern: str,
    directory: str = ".",
    path: str | None = None,
    case_sensitive: bool = False,
    use_regex: bool = False,
    include_files: str | None = None,
    exclude_files: str | None = None,
    max_results: int = 50,
    context_lines: int = 2,
    search_type: str = "smart",
    return_format: str = "string",
    output_mode: str = "content",
) -> str | list[str]:
    """Advanced parallel grep search with multiple strategies.

    Args:
        pattern: Search pattern (literal text or regex).
        directory: Directory to search (default: current directory).
        path: Alias for directory.
        case_sensitive: Whether search is case sensitive.
        use_regex: Whether pattern is a regular expression.
        include_files: File patterns to include (e.g., "*.py,*.js").
        exclude_files: File patterns to exclude.
        max_results: Maximum number of results to return.
        context_lines: Number of context lines before/after matches.
        search_type: Search strategy (smart/ripgrep/python/hybrid).
        return_format: Output format (string or list).
        output_mode: Output mode (content, files_with_matches, count, json).

    Returns:
        Formatted search results with file paths, line numbers, and context.
    """
    if path is not None:
        directory = path

    tool = ParallelGrep()
    return await tool.execute(
        pattern=pattern,
        directory=directory,
        case_sensitive=case_sensitive,
        use_regex=use_regex,
        include_files=include_files,
        exclude_files=exclude_files,
        max_results=max_results,
        context_lines=context_lines,
        search_type=search_type,
        return_format=return_format,
        output_mode=output_mode,
    )
