"""
Result formatting functionality for the grep tool.
"""

from typing import List

from .search_result import SearchConfig, SearchResult


class ResultFormatter:
    """Handles formatting of search results for display."""

    @staticmethod
    def format_results(results: List[SearchResult], pattern: str, config: SearchConfig) -> str:
        """Format search results for display."""
        if not results:
            return f"No matches found for pattern: {pattern}"

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
