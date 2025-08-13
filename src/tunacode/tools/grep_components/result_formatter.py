"""
Extended result formatter with multiple output modes for flexible presentation.
Result formatting functionality for the grep tool.
"""

from typing import Dict, List

from .search_result import SearchConfig, SearchResult


class ResultFormatter:
    """Handles formatting of search results for display with multiple output modes."""

    @staticmethod
    def format_results(
        results: List[SearchResult],
        pattern: str,
        config: SearchConfig,
        output_mode: str = "content",
    ) -> str:
        """Format search results for display.

        Args:
            results: List of search results
            pattern: Search pattern
            config: Search configuration
            output_mode: Output format mode:
                - "content": Show matching lines with context (default)
                - "files_with_matches": Show only file paths
                - "count": Show match counts per file
                - "json": JSON format for programmatic use

        Returns:
            Formatted string based on output mode
        """
        if not results:
            return f"No matches found for pattern: {pattern}"

        if output_mode == "files_with_matches":
            return ResultFormatter._format_files_only(results, pattern)
        elif output_mode == "count":
            return ResultFormatter._format_count(results, pattern)
        elif output_mode == "json":
            return ResultFormatter._format_json(results, pattern)
        else:  # Default to "content"
            return ResultFormatter._format_content(results, pattern, config)

    @staticmethod
    def _format_content(results: List[SearchResult], pattern: str, config: SearchConfig) -> str:
        """Format results with full content and context."""
        output = []
        output.append(f"Found {len(results)} matches for pattern: {pattern}")
        output.append("=" * 60)

        for result in results:
            # File header
            output.append(f"\n📁 {result.file_path}:{result.line_number}")

            # Context before
            for i, context_line in enumerate(result.context_before):
                line_num = result.line_number - len(result.context_before) + i
                output.append(f"  {line_num:4d}│ {context_line}")

            # Main match line with highlighting
            line_content = result.line_content
            before_match = line_content[: result.match_start]
            match_text = line_content[result.match_start : result.match_end]
            after_match = line_content[result.match_end :]

            output.append(f"▶ {result.line_number:4d}│ {before_match}⟨{match_text}⟩{after_match}")

            # Context after
            for i, context_line in enumerate(result.context_after):
                line_num = result.line_number + i + 1
                output.append(f"  {line_num:4d}│ {context_line}")

        return "\n".join(output)

    @staticmethod
    def _format_files_only(results: List[SearchResult], pattern: str) -> str:
        """Format results showing only file paths."""
        # Collect unique file paths
        files = sorted(set(r.file_path for r in results))

        output = []
        output.append(f"Files with matches for pattern: {pattern}")
        output.append(f"Total files: {len(files)}")
        output.append("=" * 60)

        for file_path in files:
            output.append(file_path)

        return "\n".join(output)

    @staticmethod
    def _format_count(results: List[SearchResult], pattern: str) -> str:
        """Format results showing match counts per file."""
        # Count matches per file
        file_counts: Dict[str, int] = {}
        for result in results:
            file_counts[result.file_path] = file_counts.get(result.file_path, 0) + 1

        output = []
        output.append(f"Match counts for pattern: {pattern}")
        output.append(f"Total matches: {len(results)} across {len(file_counts)} files")
        output.append("=" * 60)

        # Sort by count (descending) then by file path
        sorted_counts = sorted(file_counts.items(), key=lambda x: (-x[1], x[0]))

        for file_path, count in sorted_counts:
            output.append(f"{count:5d} {file_path}")

        return "\n".join(output)

    @staticmethod
    def _format_json(results: List[SearchResult], pattern: str) -> str:
        """Format results as JSON for programmatic use."""
        import json

        # Convert results to JSON-serializable format
        json_results = []
        for result in results:
            json_results.append(
                {
                    "file": result.file_path,
                    "line": result.line_number,
                    "content": result.line_content,
                    "match_start": result.match_start,
                    "match_end": result.match_end,
                    "context_before": result.context_before,
                    "context_after": result.context_after,
                    "score": result.relevance_score,
                }
            )

        output_data = {"pattern": pattern, "total_matches": len(results), "results": json_results}

        return json.dumps(output_data, indent=2)
