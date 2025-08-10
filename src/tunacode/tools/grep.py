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
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional, Union

from tunacode.exceptions import TooBroadPatternError, ToolExecutionError
from tunacode.tools.base import BaseTool
from tunacode.tools.grep_components import (
    FileFilter,
    PatternMatcher,
    SearchConfig,
    SearchResult,
)
from tunacode.tools.grep_components.result_formatter import ResultFormatter


class ParallelGrep(BaseTool):
    """Advanced parallel grep tool with multiple search strategies.

    CLAUDE_ANCHOR[parallel-grep-class]: Main grep implementation with timeout handling
    """

    def __init__(self, ui_logger=None):
        super().__init__(ui_logger)
        self._executor = ThreadPoolExecutor(max_workers=8)
        self._file_filter = FileFilter()
        self._pattern_matcher = PatternMatcher()
        self._result_formatter = ResultFormatter()

    @property
    def tool_name(self) -> str:
        return "grep"

    async def _execute(
        self,
        pattern: str,
        directory: str = ".",
        case_sensitive: bool = False,
        use_regex: bool = False,
        include_files: Optional[str] = None,
        exclude_files: Optional[str] = None,
        max_results: int = 50,
        context_lines: int = 2,
        search_type: str = "smart",  # smart, ripgrep, python, hybrid
        return_format: str = "string",  # "string" (default) or "list" (legacy)
    ) -> Union[str, List[str]]:
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
            # 1️⃣ Fast-glob prefilter to find candidate files
            include_pattern = include_files or "*"
            exclude_pattern = exclude_files

            candidates = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._file_filter.fast_glob,
                Path(directory),
                include_pattern,
                exclude_pattern,
            )

            if not candidates:
                if return_format == "list":
                    return []
                return f"No files found matching pattern: {include_pattern}"

            # 2️⃣ Smart strategy selection based on candidate count
            original_search_type = search_type
            if search_type == "smart":
                if len(candidates) <= 50:
                    # Small set - Python strategy more efficient (low startup cost)
                    search_type = "python"
                elif len(candidates) <= 1000:
                    # Medium set - Ripgrep optimal for this range
                    search_type = "ripgrep"
                else:
                    # Large set - Hybrid for best coverage and redundancy
                    search_type = "hybrid"

            # 3️⃣ Create search configuration
            # Note: include_patterns/exclude_patterns now only used for legacy compatibility
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

            # 4️⃣ Execute chosen strategy with pre-filtered candidates
            # Execute search with pre-filtered candidates
            if search_type == "ripgrep":
                # Try ripgrep first for performance. If ripgrep is unavailable or
                # returns no results (e.g., binary missing), gracefully fallback to
                # the Python implementation so the tool still returns matches.
                results = await self._ripgrep_search_filtered(pattern, candidates, config)
                if not results:
                    # Fallback to python search when ripgrep produced no output
                    results = await self._python_search_filtered(pattern, candidates, config)
            elif search_type == "python":
                results = await self._python_search_filtered(pattern, candidates, config)
            elif search_type == "hybrid":
                results = await self._hybrid_search_filtered(pattern, candidates, config)
            else:
                raise ToolExecutionError(f"Unknown search type: {search_type}")

            # 5️⃣ Format and return results with strategy info
            strategy_info = f"Strategy: {search_type} (was {original_search_type}), Files: {len(candidates)}/{5000}"
            formatted_results = self._result_formatter.format_results(results, pattern, config)

            if return_format == "list":
                # Legacy: return list of file paths with at least one match
                file_set = set()
                for r in results:
                    file_set.add(r.file_path)
                return list(file_set)
            else:
                # Add strategy info to results
                if formatted_results.startswith("Found"):
                    lines = formatted_results.split("\n")
                    lines[1] = (
                        f"Strategy: {search_type} | Candidates: {len(candidates)} files | "
                        + lines[1]
                    )
                    return "\n".join(lines)
                else:
                    return f"{formatted_results}\n\n{strategy_info}"

        except TooBroadPatternError:
            # Re-raise TooBroadPatternError without wrapping it
            raise
        except Exception as e:
            raise ToolExecutionError(f"Grep search failed: {str(e)}")

    # ====== SEARCH METHODS ======

    async def _ripgrep_search_filtered(
        self, pattern: str, candidates: List[Path], config: SearchConfig
    ) -> List[SearchResult]:
        """
        Run ripgrep on pre-filtered file list with first match deadline.
        """

        def run_ripgrep_filtered():
            cmd = ["rg", "--json"]

            # Add configuration flags
            if not config.case_sensitive:
                cmd.append("--ignore-case")
            if config.context_lines > 0:
                cmd.extend(["--context", str(config.context_lines)])
            if config.max_results:
                cmd.extend(["--max-count", str(config.max_results)])

            # Add pattern and explicit file list
            cmd.append(pattern)
            cmd.extend(str(f) for f in candidates)

            try:
                # Start the process
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
                )

                # Monitor for first match within deadline
                start_time = time.time()
                output_lines = []
                first_match_found = False

                while True:
                    # Check if we exceeded the first match deadline
                    if (
                        not first_match_found
                        and (time.time() - start_time) > config.first_match_deadline
                    ):
                        process.kill()
                        process.wait()
                        raise TooBroadPatternError(pattern, config.first_match_deadline)

                    # Check if process is still running
                    if process.poll() is not None:
                        # Process finished, get any remaining output
                        remaining_output, _ = process.communicate()
                        if remaining_output:
                            output_lines.extend(remaining_output.splitlines())
                        break

                    # Try to read a line (non-blocking)
                    try:
                        # Use a small timeout to avoid blocking indefinitely
                        line = process.stdout.readline()
                        if line:
                            output_lines.append(line.rstrip())
                            # Check if this is a match line
                            if '"type":"match"' in line:
                                first_match_found = True
                    except Exception:
                        pass

                    # Small sleep to avoid busy waiting
                    time.sleep(0.01)

                # Check exit code
                if process.returncode == 0 or output_lines:
                    # Return output even if exit code is non-zero but we have matches
                    return "\n".join(output_lines)
                else:
                    return None

            except TooBroadPatternError:
                raise
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None
            except Exception:
                # Make sure to clean up the process
                if "process" in locals():
                    try:
                        process.kill()
                        process.wait()
                    except Exception:
                        pass
                return None

        # Run ripgrep with monitoring in thread pool
        try:
            output = await asyncio.get_event_loop().run_in_executor(
                self._executor, run_ripgrep_filtered
            )
            if output:
                parsed = self._pattern_matcher.parse_ripgrep_output(output)
                return parsed
            return []
        except TooBroadPatternError:
            raise

    async def _python_search_filtered(
        self, pattern: str, candidates: List[Path], config: SearchConfig
    ) -> List[SearchResult]:
        """
        Run Python parallel search on pre-filtered candidates with first match deadline.
        """
        # Prepare search pattern
        if config.use_regex:
            flags = 0 if config.case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(pattern, flags)
        else:
            regex_pattern = None

        # Track search progress
        first_match_event = asyncio.Event()

        async def search_with_monitoring(file_path: Path):
            """Search a file and signal when first match is found."""
            try:
                file_results = await self._search_file(file_path, pattern, regex_pattern, config)
                if file_results and not first_match_event.is_set():
                    first_match_event.set()
                return file_results
            except Exception:
                return []

        # Create search tasks for candidates only
        search_tasks = []
        for file_path in candidates:
            task = search_with_monitoring(file_path)
            search_tasks.append(task)

        # Create a deadline task
        async def check_deadline():
            """Monitor for first match deadline."""
            await asyncio.sleep(config.first_match_deadline)
            if not first_match_event.is_set():
                # Cancel all pending tasks
                for task in search_tasks:
                    if not task.done():
                        task.cancel()
                raise TooBroadPatternError(pattern, config.first_match_deadline)

        deadline_task = asyncio.create_task(check_deadline())

        try:
            # Execute searches in parallel with deadline monitoring
            all_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Cancel deadline task if we got results
            deadline_task.cancel()

            # Flatten results and filter out exceptions
            results = []
            for file_results in all_results:
                if isinstance(file_results, list):
                    results.extend(file_results)

            # Sort by relevance and limit results
            results.sort(key=lambda r: r.relevance_score, reverse=True)
            return results[: config.max_results]

        except asyncio.CancelledError:
            # Re-raise TooBroadPatternError if that's what caused the cancellation
            if deadline_task.done():
                try:
                    await deadline_task
                except TooBroadPatternError:
                    raise
            return []

    async def _hybrid_search_filtered(
        self, pattern: str, candidates: List[Path], config: SearchConfig
    ) -> List[SearchResult]:
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
        regex_pattern: Optional[re.Pattern],
        config: SearchConfig,
    ) -> List[SearchResult]:
        """Search a single file for the pattern."""

        def search_file_sync():
            return self._pattern_matcher.search_file(file_path, pattern, regex_pattern, config)

        return await asyncio.get_event_loop().run_in_executor(self._executor, search_file_sync)


# Create tool instance for pydantic-ai
async def grep(
    pattern: str,
    directory: str = ".",
    path: Optional[str] = None,  # Alias for directory
    case_sensitive: bool = False,
    use_regex: bool = False,
    include_files: Optional[str] = None,
    exclude_files: Optional[str] = None,
    max_results: int = 50,
    context_lines: int = 2,
    search_type: str = "smart",
    return_format: str = "string",
) -> Union[str, List[str]]:
    """
    Advanced parallel grep search with multiple strategies.

    Args:
        pattern: Search pattern (literal text or regex)
        directory: Directory to search (default: current directory)
        case_sensitive: Whether search is case sensitive (default: False)
        use_regex: Whether pattern is a regular expression (default: False)
        include_files: File patterns to include, comma-separated (e.g., "*.py,*.js")
        exclude_files: File patterns to exclude, comma-separated (e.g., "*.pyc,node_modules/*")
        max_results: Maximum number of results to return (default: 50)
        context_lines: Number of context lines before/after matches (default: 2)
        search_type: Search strategy - "smart", "ripgrep", "python", or "hybrid" (default: "smart")

    Returns:
        Formatted search results with file paths, line numbers, and context

    Examples:
        grep("TODO", ".", max_results=20)
        grep("function.*export", "src/", use_regex=True, include_files="*.js,*.ts")
        grep("import.*pandas", ".", include_files="*.py", search_type="hybrid")
    """
    # Handle path alias for directory
    if path is not None:
        directory = path

    tool = ParallelGrep()
    return await tool._execute(
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
    )
