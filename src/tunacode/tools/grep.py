"""
Parallel grep tool for TunaCode - Enhanced content search with parallel processing.

This tool provides sophisticated grep-like functionality with:
- Parallel file searching across multiple directories
- Multiple search strategies (literal, regex, fuzzy)
- Smart result ranking and deduplication
- Context-aware output formatting
"""

import asyncio
import re
import subprocess
import fnmatch
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from tunacode.tools.base import BaseTool
from tunacode.exceptions import ToolExecutionError


@dataclass
class SearchResult:
    """Represents a single search match with context."""
    file_path: str
    line_number: int
    line_content: str
    match_start: int
    match_end: int
    context_before: List[str]
    context_after: List[str]
    relevance_score: float = 0.0


@dataclass
class SearchConfig:
    """Configuration for search operations."""
    case_sensitive: bool = False
    use_regex: bool = False
    max_results: int = 50
    context_lines: int = 2
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_file_size: int = 1024 * 1024  # 1MB
    timeout_seconds: int = 30


# Fast-Glob Prefilter Configuration
MAX_GLOB = 5_000        # Hard cap - protects memory & tokens
GLOB_BATCH = 500        # Streaming batch size
EXCLUDE_DIRS = {        # Common directories to skip
    'node_modules', '.git', '__pycache__', 
    '.venv', 'venv', 'dist', 'build', '.pytest_cache',
    '.mypy_cache', '.tox', 'target', 'node_modules'
}


def fast_glob(root: Path, include: str, exclude: str = None) -> List[Path]:
    """
    Lightning-fast filename filtering using os.scandir.
    
    Args:
        root: Directory to search
        include: Include pattern (e.g., "*.py", "*.{js,ts}")
        exclude: Exclude pattern (optional)
    
    Returns:
        List of matching file paths (bounded by MAX_GLOB)
    """
    matches, stack = [], [root]
    
    # Handle multiple extensions in include pattern like "*.{py,js,ts}"
    if '{' in include and '}' in include:
        # Convert *.{py,js,ts} to multiple patterns
        base, ext_part = include.split('{', 1)
        ext_part = ext_part.split('}', 1)[0]
        extensions = ext_part.split(',')
        include_patterns = [base + ext.strip() for ext in extensions]
        include_regexes = [re.compile(fnmatch.translate(pat), re.IGNORECASE) for pat in include_patterns]
    else:
        include_regexes = [re.compile(fnmatch.translate(include), re.IGNORECASE)]
    
    exclude_rx = re.compile(fnmatch.translate(exclude), re.IGNORECASE) if exclude else None
    
    while stack and len(matches) < MAX_GLOB:
        current_dir = stack.pop()
        
        try:
            with os.scandir(current_dir) as entries:
                for entry in entries:
                    # Skip common irrelevant directories
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name not in EXCLUDE_DIRS:
                            stack.append(Path(entry.path))
                    
                    # Check file matches
                    elif entry.is_file(follow_symlinks=False):
                        # Check against any include pattern
                        matches_include = any(regex.match(entry.name) for regex in include_regexes)
                        
                        if matches_include:
                            if not exclude_rx or not exclude_rx.match(entry.name):
                                matches.append(Path(entry.path))
                                
        except (PermissionError, OSError):
            continue  # Skip inaccessible directories
            
    return matches[:MAX_GLOB]


class ParallelGrep(BaseTool):
    """Advanced parallel grep tool with multiple search strategies."""
    
    def __init__(self, ui_logger=None):
        super().__init__(ui_logger)
        self._executor = ThreadPoolExecutor(max_workers=8)
        
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
        search_type: str = "smart"  # smart, ripgrep, python, hybrid
    ) -> str:
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
                fast_glob, 
                Path(directory), 
                include_pattern,
                exclude_pattern
            )
            
            if not candidates:
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
            include_patterns = self._parse_patterns(include_files) if include_files else ["*"]
            exclude_patterns = self._parse_patterns(exclude_files) if exclude_files else []
            config = SearchConfig(
                case_sensitive=case_sensitive,
                use_regex=use_regex,
                max_results=max_results,
                context_lines=context_lines,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
            
            # 4️⃣ Execute chosen strategy with pre-filtered candidates
            if search_type == "ripgrep":
                results = await self._ripgrep_search_filtered(pattern, candidates, config)
            elif search_type == "python":
                results = await self._python_search_filtered(pattern, candidates, config)
            elif search_type == "hybrid":
                results = await self._hybrid_search_filtered(pattern, candidates, config)
            else:
                raise ToolExecutionError(f"Unknown search type: {search_type}")
            
            # 5️⃣ Format and return results with strategy info
            strategy_info = f"Strategy: {search_type} (was {original_search_type}), Files: {len(candidates)}/{MAX_GLOB}"
            formatted_results = self._format_results(results, pattern, config)
            
            # Add strategy info to results
            if formatted_results.startswith("Found"):
                lines = formatted_results.split('\n')
                lines[1] = f"Strategy: {search_type} | Candidates: {len(candidates)} files | " + lines[1]
                return '\n'.join(lines)
            else:
                return f"{formatted_results}\n\n{strategy_info}"
            
        except Exception as e:
            raise ToolExecutionError(f"Grep search failed: {str(e)}")
    
    async def _smart_search(
        self, 
        pattern: str, 
        directory: str, 
        config: SearchConfig
    ) -> List[SearchResult]:
        """Smart search that chooses optimal strategy based on context."""
        
        # Try ripgrep first (fastest for large codebases)
        try:
            results = await self._ripgrep_search(pattern, directory, config)
            if results:
                return results
        except:
            pass
        
        # Fallback to Python implementation
        return await self._python_search(pattern, directory, config)
    
    async def _ripgrep_search(
        self, 
        pattern: str, 
        directory: str, 
        config: SearchConfig
    ) -> List[SearchResult]:
        """Use ripgrep for high-performance searching."""
        
        def run_ripgrep():
            cmd = ["rg", "--json"]
            
            # Add options based on config
            if not config.case_sensitive:
                cmd.append("--ignore-case")
            if config.context_lines > 0:
                cmd.extend(["--context", str(config.context_lines)])
            if config.max_results:
                cmd.extend(["--max-count", str(config.max_results)])
            
            # Add include/exclude patterns
            for pattern_str in config.include_patterns:
                if pattern_str != "*":
                    cmd.extend(["--glob", pattern_str])
            for pattern_str in config.exclude_patterns:
                cmd.extend(["--glob", f"!{pattern_str}"])
            
            # Add pattern and directory
            cmd.extend([pattern, directory])
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout_seconds
                )
                return result.stdout if result.returncode == 0 else None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None
        
        # Run ripgrep in thread pool
        output = await asyncio.get_event_loop().run_in_executor(
            self._executor, run_ripgrep
        )
        
        if not output:
            return []
        
        # Parse ripgrep JSON output
        return self._parse_ripgrep_output(output)
    
    async def _python_search(
        self, 
        pattern: str, 
        directory: str, 
        config: SearchConfig
    ) -> List[SearchResult]:
        """Pure Python parallel search implementation."""
        
        # Find all files to search
        files = await self._find_files(directory, config)
        
        # Prepare search pattern
        if config.use_regex:
            flags = 0 if config.case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(pattern, flags)
        else:
            regex_pattern = None
        
        # Create search tasks for parallel execution
        search_tasks = []
        for file_path in files:
            task = self._search_file(
                file_path, pattern, regex_pattern, config
            )
            search_tasks.append(task)
        
        # Execute searches in parallel
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        results = []
        for file_results in all_results:
            if isinstance(file_results, list):
                results.extend(file_results)
        
        # Sort by relevance and limit results
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:config.max_results]
    
    async def _hybrid_search(
        self, 
        pattern: str, 
        directory: str, 
        config: SearchConfig
    ) -> List[SearchResult]:
        """Hybrid approach using multiple search methods concurrently."""
        
        # Run multiple search strategies in parallel
        tasks = [
            self._ripgrep_search(pattern, directory, config),
            self._python_search(pattern, directory, config)
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
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
        return unique_results[:config.max_results]
    
    # ====== NEW FILTERED SEARCH METHODS ======
    
    async def _ripgrep_search_filtered(
        self, 
        pattern: str, 
        candidates: List[Path], 
        config: SearchConfig
    ) -> List[SearchResult]:
        """
        Run ripgrep on pre-filtered file list.
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
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=config.timeout_seconds
                )
                return result.stdout if result.returncode == 0 else None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None
        
        # Run ripgrep in thread pool
        output = await asyncio.get_event_loop().run_in_executor(
            self._executor, run_ripgrep_filtered
        )
        
        return self._parse_ripgrep_output(output) if output else []
    
    async def _python_search_filtered(
        self, 
        pattern: str, 
        candidates: List[Path], 
        config: SearchConfig
    ) -> List[SearchResult]:
        """
        Run Python parallel search on pre-filtered candidates.
        """
        # Prepare search pattern
        if config.use_regex:
            flags = 0 if config.case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(pattern, flags)
        else:
            regex_pattern = None
        
        # Create search tasks for candidates only
        search_tasks = []
        for file_path in candidates:
            task = self._search_file(
                file_path, pattern, regex_pattern, config
            )
            search_tasks.append(task)
        
        # Execute searches in parallel
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Flatten results and filter out exceptions
        results = []
        for file_results in all_results:
            if isinstance(file_results, list):
                results.extend(file_results)
        
        # Sort by relevance and limit results
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:config.max_results]
    
    async def _hybrid_search_filtered(
        self, 
        pattern: str, 
        candidates: List[Path], 
        config: SearchConfig
    ) -> List[SearchResult]:
        """
        Hybrid approach using multiple search methods concurrently on pre-filtered candidates.
        """
        
        # Run multiple search strategies in parallel
        tasks = [
            self._ripgrep_search_filtered(pattern, candidates, config),
            self._python_search_filtered(pattern, candidates, config)
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
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
        return unique_results[:config.max_results]
    
    async def _find_files(
        self, 
        directory: str, 
        config: SearchConfig
    ) -> List[Path]:
        """Find all files matching include/exclude patterns."""
        
        def find_files_sync():
            files = []
            dir_path = Path(directory)
            
            for file_path in dir_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                # Check file size
                try:
                    if file_path.stat().st_size > config.max_file_size:
                        continue
                except OSError:
                    continue
                
                # Check include patterns
                if not any(fnmatch.fnmatch(str(file_path), pattern) 
                          for pattern in config.include_patterns):
                    continue
                
                # Check exclude patterns
                if any(fnmatch.fnmatch(str(file_path), pattern) 
                      for pattern in config.exclude_patterns):
                    continue
                
                files.append(file_path)
            
            return files
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, find_files_sync
        )
    
    async def _search_file(
        self,
        file_path: Path,
        pattern: str,
        regex_pattern: Optional[re.Pattern],
        config: SearchConfig
    ) -> List[SearchResult]:
        """Search a single file for the pattern."""
        
        def search_file_sync():
            try:
                with file_path.open('r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                results = []
                for i, line in enumerate(lines):
                    line = line.rstrip('\n\r')
                    
                    # Search for pattern
                    if regex_pattern:
                        matches = list(regex_pattern.finditer(line))
                    else:
                        # Simple string search
                        search_line = line if config.case_sensitive else line.lower()
                        search_pattern = pattern if config.case_sensitive else pattern.lower()
                        
                        matches = []
                        start = 0
                        while True:
                            pos = search_line.find(search_pattern, start)
                            if pos == -1:
                                break
                            # Create a simple match object
                            class SimpleMatch:
                                def __init__(self, start_pos, end_pos):
                                    self._start = start_pos
                                    self._end = end_pos
                                def start(self):
                                    return self._start
                                def end(self):
                                    return self._end
                            match = SimpleMatch(pos, pos + len(search_pattern))
                            matches.append(match)
                            start = pos + 1
                    
                    # Create results for each match
                    for match in matches:
                        # Get context lines
                        context_start = max(0, i - config.context_lines)
                        context_end = min(len(lines), i + config.context_lines + 1)
                        
                        context_before = [
                            lines[j].rstrip('\n\r') 
                            for j in range(context_start, i)
                        ]
                        context_after = [
                            lines[j].rstrip('\n\r') 
                            for j in range(i + 1, context_end)
                        ]
                        
                        # Calculate relevance score
                        relevance = self._calculate_relevance(
                            str(file_path), line, pattern, match
                        )
                        
                        result = SearchResult(
                            file_path=str(file_path),
                            line_number=i + 1,
                            line_content=line,
                            match_start=match.start() if hasattr(match, 'start') else match.start(),
                            match_end=match.end() if hasattr(match, 'end') else match.end(),
                            context_before=context_before,
                            context_after=context_after,
                            relevance_score=relevance
                        )
                        results.append(result)
                
                return results
                
            except Exception:
                return []
        
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, search_file_sync
        )
    
    def _calculate_relevance(
        self, 
        file_path: str, 
        line: str, 
        pattern: str, 
        match
    ) -> float:
        """Calculate relevance score for a search result."""
        score = 0.0
        
        # Base score
        score += 1.0
        
        # Boost for exact matches
        if pattern.lower() in line.lower():
            score += 0.5
        
        # Boost for matches at word boundaries
        if match.start() == 0 or not line[match.start() - 1].isalnum():
            score += 0.3
        
        # Boost for certain file types
        if file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
            score += 0.2
        
        # Boost for matches in comments or docstrings
        stripped_line = line.strip()
        if stripped_line.startswith(('#', '//', '/*', '"""', "'''")):
            score += 0.1
        
        return score
    
    def _parse_ripgrep_output(self, output: str) -> List[SearchResult]:
        """Parse ripgrep JSON output into SearchResult objects."""
        import json
        
        results = []
        for line in output.strip().split('\n'):
            if not line:
                continue
            
            try:
                data = json.loads(line)
                if data.get('type') != 'match':
                    continue
                
                match_data = data['data']
                result = SearchResult(
                    file_path=match_data['path']['text'],
                    line_number=match_data['line_number'],
                    line_content=match_data['lines']['text'].rstrip('\n\r'),
                    match_start=match_data['submatches'][0]['start'],
                    match_end=match_data['submatches'][0]['end'],
                    context_before=[],  # Ripgrep context handling would go here
                    context_after=[],
                    relevance_score=1.0
                )
                results.append(result)
            except (json.JSONDecodeError, KeyError):
                continue
        
        return results
    
    def _parse_patterns(self, patterns: str) -> List[str]:
        """Parse comma-separated file patterns."""
        return [p.strip() for p in patterns.split(',') if p.strip()]
    
    def _format_results(
        self, 
        results: List[SearchResult], 
        pattern: str, 
        config: SearchConfig
    ) -> str:
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
            before_match = line_content[:result.match_start]
            match_text = line_content[result.match_start:result.match_end]
            after_match = line_content[result.match_end:]
            
            output.append(f"▶ {result.line_number:4d}│ {before_match}⟨{match_text}⟩{after_match}")
            
            # Context after
            for i, context_line in enumerate(result.context_after):
                line_num = result.line_number + i + 1
                output.append(f"  {line_num:4d}│ {context_line}")
        
        return "\n".join(output)


# Create tool instance for pydantic-ai
async def grep(
    pattern: str,
    directory: str = ".",
    case_sensitive: bool = False,
    use_regex: bool = False,
    include_files: Optional[str] = None,
    exclude_files: Optional[str] = None,
    max_results: int = 50,
    context_lines: int = 2,
    search_type: str = "smart"
) -> str:
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
        search_type=search_type
    )