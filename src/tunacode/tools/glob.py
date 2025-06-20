"""
Glob tool for fast file pattern matching.

This tool provides filesystem pattern matching capabilities using glob patterns,
complementing the grep tool's content search with fast filename-based searching.
"""

import asyncio
import fnmatch
import os
from pathlib import Path
from typing import List, Optional

from tunacode.exceptions import ToolExecutionError
from tunacode.tools.base import BaseTool

# Configuration
MAX_RESULTS = 5000  # Maximum files to return
EXCLUDE_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "target",
    ".next",
    ".nuxt",
    "coverage",
    ".coverage",
}


class GlobTool(BaseTool):
    """Fast file pattern matching tool using glob patterns."""

    @property
    def tool_name(self) -> str:
        return "glob"

    async def _execute(
        self,
        pattern: str,
        directory: str = ".",
        recursive: bool = True,
        include_hidden: bool = False,
        exclude_dirs: Optional[List[str]] = None,
        max_results: int = MAX_RESULTS,
    ) -> str:
        """
        Find files matching glob patterns.

        Args:
            pattern: Glob pattern to match (e.g., "*.py", "**/*.{js,ts}", "src/**/test_*.py")
            directory: Directory to search in (default: current directory)
            recursive: Whether to search recursively (default: True)
            include_hidden: Whether to include hidden files/directories (default: False)
            exclude_dirs: Additional directories to exclude from search
            max_results: Maximum number of results to return (default: 5000)

        Returns:
            List of matching file paths as a formatted string

        Examples:
            glob("*.py")                    # All Python files in current directory
            glob("**/*.py", recursive=True) # All Python files recursively
            glob("*.{js,ts,jsx,tsx}")       # Multiple extensions
            glob("src/**/test_*.py")        # Test files in src directory
            glob("docs/**/*.md")            # All markdown files in docs
        """
        try:
            # Parse the directory path
            root_path = Path(directory).resolve()
            if not root_path.exists():
                return f"Error: Directory '{directory}' does not exist"
            if not root_path.is_dir():
                return f"Error: '{directory}' is not a directory"

            # Combine default and custom exclude directories
            all_exclude_dirs = EXCLUDE_DIRS.copy()
            if exclude_dirs:
                all_exclude_dirs.update(exclude_dirs)

            # Handle multiple extensions pattern like "*.{py,js,ts}"
            patterns = self._expand_brace_pattern(pattern)

            # Perform the glob search
            matches = await self._glob_search(
                root_path, patterns, recursive, include_hidden, all_exclude_dirs, max_results
            )

            # Format results
            if not matches:
                return f"No files found matching pattern: {pattern}"

            # Sort matches by path
            matches.sort()

            # Create formatted output
            output = []
            output.append(f"Found {len(matches)} files matching pattern: {pattern}")
            if len(matches) == max_results:
                output.append(f"(Results limited to {max_results} files)")
            output.append("=" * 60)

            # Group files by directory for better readability
            current_dir = None
            for match in matches:
                match_dir = os.path.dirname(match)
                if match_dir != current_dir:
                    if current_dir is not None:
                        output.append("")  # Empty line between directories
                    output.append(f"📁 {match_dir}/")
                    current_dir = match_dir

                filename = os.path.basename(match)
                output.append(f"  - {filename}")

            return "\n".join(output)

        except Exception as e:
            raise ToolExecutionError(f"Glob search failed: {str(e)}")

    def _expand_brace_pattern(self, pattern: str) -> List[str]:
        """
        Expand brace patterns like "*.{py,js,ts}" into multiple patterns.

        Args:
            pattern: Pattern that may contain braces

        Returns:
            List of expanded patterns
        """
        if "{" not in pattern or "}" not in pattern:
            return [pattern]

        # Find the brace expression
        start = pattern.find("{")
        end = pattern.find("}")

        if start == -1 or end == -1 or end < start:
            return [pattern]

        # Extract parts
        prefix = pattern[:start]
        suffix = pattern[end + 1 :]
        options = pattern[start + 1 : end].split(",")

        # Generate all combinations
        patterns = []
        for option in options:
            patterns.append(prefix + option.strip() + suffix)

        return patterns

    async def _glob_search(
        self,
        root: Path,
        patterns: List[str],
        recursive: bool,
        include_hidden: bool,
        exclude_dirs: set,
        max_results: int,
    ) -> List[str]:
        """
        Perform the actual glob search using os.scandir for speed.

        Args:
            root: Root directory to search
            patterns: List of glob patterns to match
            recursive: Whether to search recursively
            include_hidden: Whether to include hidden files
            exclude_dirs: Set of directory names to exclude
            max_results: Maximum results to return

        Returns:
            List of matching file paths
        """

        def search_sync():
            matches = []
            stack = [root]

            # Compile patterns to regex for faster matching
            compiled_patterns = []
            for pat in patterns:
                # Handle ** for recursive matching
                if "**" in pat:
                    # Convert ** to match any path depth
                    regex_pat = pat.replace("**", "__STARSTAR__")
                    regex_pat = fnmatch.translate(regex_pat)
                    regex_pat = regex_pat.replace("__STARSTAR__", ".*")
                    compiled_patterns.append((pat, re.compile(regex_pat, re.IGNORECASE)))
                else:
                    compiled_patterns.append(
                        (pat, re.compile(fnmatch.translate(pat), re.IGNORECASE))
                    )

            while stack and len(matches) < max_results:
                current_dir = stack.pop()

                try:
                    with os.scandir(current_dir) as entries:
                        for entry in entries:
                            # Skip hidden files/dirs if not included
                            if not include_hidden and entry.name.startswith("."):
                                continue

                            if entry.is_dir(follow_symlinks=False):
                                # Check if directory should be excluded
                                if entry.name not in exclude_dirs and recursive:
                                    stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                # Check against patterns
                                rel_path = os.path.relpath(entry.path, root)

                                for original_pat, compiled_pat in compiled_patterns:
                                    # For ** patterns, match against full relative path
                                    if "**" in original_pat:
                                        if compiled_pat.match(rel_path):
                                            matches.append(entry.path)
                                            break
                                    else:
                                        # For simple patterns, match against filename only
                                        if compiled_pat.match(entry.name):
                                            matches.append(entry.path)
                                            break

                                if len(matches) >= max_results:
                                    break

                except (PermissionError, OSError):
                    # Skip directories we can't read
                    continue

            return matches[:max_results]

        # Import re here to avoid issues at module level
        import re

        # Run the synchronous search in the thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, search_sync)


# Create the tool function for pydantic-ai
async def glob(
    pattern: str,
    directory: str = ".",
    recursive: bool = True,
    include_hidden: bool = False,
    exclude_dirs: Optional[List[str]] = None,
    max_results: int = MAX_RESULTS,
) -> str:
    """
    Find files matching glob patterns with fast filesystem traversal.

    Args:
        pattern: Glob pattern to match (e.g., "*.py", "**/*.{js,ts}", "src/**/test_*.py")
        directory: Directory to search in (default: current directory)
        recursive: Whether to search recursively (default: True)
        include_hidden: Whether to include hidden files/directories (default: False)
        exclude_dirs: Additional directories to exclude from search (default: common build/cache dirs)
        max_results: Maximum number of results to return (default: 5000)

    Returns:
        Formatted list of matching file paths grouped by directory

    Examples:
        glob("*.py")                         # All Python files in current directory
        glob("**/*.py")                      # All Python files recursively
        glob("*.{js,ts,jsx,tsx}")            # Multiple extensions
        glob("src/**/test_*.py")             # Test files in src directory
        glob("**/*.md", include_hidden=True) # Include hidden directories
    """
    tool = GlobTool()
    return await tool._execute(
        pattern=pattern,
        directory=directory,
        recursive=recursive,
        include_hidden=include_hidden,
        exclude_dirs=exclude_dirs,
        max_results=max_results,
    )
