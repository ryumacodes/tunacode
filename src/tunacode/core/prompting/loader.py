"""Section loader for prompt templates."""

from pathlib import Path

from .sections import SystemPromptSection


class SectionLoader:
    """Loads prompt section content from files.

    Supports .xml, .md, and .txt file extensions.
    Uses mtime-based caching for efficiency.
    """

    EXTENSIONS = (".xml", ".md", ".txt")

    def __init__(self, sections_dir: Path) -> None:
        self.sections_dir = sections_dir
        self._cache: dict[str, tuple[str, float]] = {}

    def load_section(self, section: SystemPromptSection) -> str:
        """Load a section's content from file.

        Args:
            section: The section to load

        Returns:
            Section content, or empty string if not found
        """
        filename = section.value.lower()
        for ext in self.EXTENSIONS:
            path = self.sections_dir / f"{filename}{ext}"
            if path.exists():
                return self._read_with_cache(path)
        return ""

    def load_all(self) -> dict[str, str]:
        """Load all sections into a dict.

        Returns:
            Dict mapping section name to content
        """
        return {s.value: self.load_section(s) for s in SystemPromptSection}

    def _read_with_cache(self, path: Path) -> str:
        """Read file with mtime-based cache invalidation.

        Args:
            path: File path to read

        Returns:
            File contents
        """
        key = str(path)
        mtime = path.stat().st_mtime
        if key in self._cache:
            cached_content, cached_mtime = self._cache[key]
            if cached_mtime == mtime:
                return cached_content
        content = path.read_text()
        self._cache[key] = (content, mtime)
        return content

    def clear_cache(self) -> None:
        """Clear the file cache."""
        self._cache.clear()
