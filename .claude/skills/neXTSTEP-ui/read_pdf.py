#!/usr/bin/env python3
"""Read NeXTSTEP UI Guidelines PDF in chunks.

Usage:
    python read_pdf.py                    # List all pages with titles
    python read_pdf.py 1                  # Read page 1
    python read_pdf.py 1-10               # Read pages 1 through 10
    python read_pdf.py 15 20 25           # Read specific pages
    python read_pdf.py --search "button"  # Search for text
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("pypdf not installed. Run: uv pip install pypdf")

PDF_PATH = Path(__file__).parent / "NeXTSTEP_User_Interface_Guidelines_Release_3_Nov93.pdf"
CHARS_PER_CHUNK = 8000


def get_reader() -> PdfReader:
    """Load the PDF reader."""
    if not PDF_PATH.exists():
        sys.exit(f"PDF not found: {PDF_PATH}")
    return PdfReader(PDF_PATH)


def extract_page(reader: PdfReader, page_num: int) -> str:
    """Extract text from a single page (1-indexed)."""
    if page_num < 1 or page_num > len(reader.pages):
        return f"[Page {page_num} out of range. PDF has {len(reader.pages)} pages.]"

    page = reader.pages[page_num - 1]
    text = page.extract_text() or "[No text extracted]"
    return f"--- Page {page_num}/{len(reader.pages)} ---\n{text}"


def list_pages(reader: PdfReader) -> str:
    """List all pages with preview of first line."""
    lines = [f"NeXTSTEP User Interface Guidelines - {len(reader.pages)} pages\n"]

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        first_line = text.split("\n")[0][:60] if text else "[empty]"
        lines.append(f"  {i:3d}: {first_line}...")

    return "\n".join(lines)


def search_text(reader: PdfReader, query: str) -> str:
    """Search for text across all pages."""
    query_lower = query.lower()
    results = []

    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if query_lower in text.lower():
            # Find matching lines
            for line in text.split("\n"):
                if query_lower in line.lower():
                    results.append(f"  p{i}: {line.strip()[:80]}")

    if not results:
        return f"No matches for '{query}'"

    return f"Found {len(results)} matches for '{query}':\n" + "\n".join(results[:50])


def parse_page_range(arg: str, max_pages: int) -> list[int]:
    """Parse page range like '1-10' or single page '5'."""
    if "-" in arg:
        start, end = arg.split("-", 1)
        start = max(1, int(start))
        end = min(max_pages, int(end))
        return list(range(start, end + 1))
    return [int(arg)]


def main():
    parser = argparse.ArgumentParser(description="Read NeXTSTEP PDF in chunks")
    parser.add_argument("pages", nargs="*", help="Page numbers or ranges (e.g., 1 5-10)")
    parser.add_argument("--search", "-s", help="Search for text in PDF")
    parser.add_argument("--list", "-l", action="store_true", help="List all pages")
    args = parser.parse_args()

    reader = get_reader()

    if args.search:
        print(search_text(reader, args.search))
        return

    if args.list or not args.pages:
        print(list_pages(reader))
        return

    # Parse and read requested pages
    pages_to_read: list[int] = []
    for arg in args.pages:
        pages_to_read.extend(parse_page_range(arg, len(reader.pages)))

    # Dedupe and sort
    pages_to_read = sorted(set(pages_to_read))

    output = []
    for page_num in pages_to_read:
        output.append(extract_page(reader, page_num))

    print("\n\n".join(output))


if __name__ == "__main__":
    main()
