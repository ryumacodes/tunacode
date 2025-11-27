"""
Module: tunacode.tools.edit_replacers

Fuzzy string replacement strategies for the update_file tool.
Inspired by:
- https://github.com/cline/cline/blob/main/evals/diff-edits/diff-apply/diff-06-23-25.ts
- https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/utils/editCorrector.ts
- https://github.com/sst/opencode/blob/dev/packages/opencode/src/tool/edit.ts

Each replacer is a generator that yields potential matches found in content.
Replacers are tried in order from strict to fuzzy until one succeeds.
"""

from typing import Callable, Generator

# Type alias for replacer functions
Replacer = Callable[[str, str], Generator[str, None, None]]

# Similarity thresholds for block anchor fallback matching
SINGLE_CANDIDATE_SIMILARITY_THRESHOLD = 0.0
MULTIPLE_CANDIDATES_SIMILARITY_THRESHOLD = 0.3


def levenshtein(a: str, b: str) -> int:
    """Levenshtein distance algorithm for fuzzy matching.

    Args:
        a: First string
        b: Second string

    Returns:
        Edit distance between the two strings
    """
    if not a or not b:
        return max(len(a), len(b))

    matrix = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        matrix[i][0] = i
    for j in range(len(b) + 1):
        matrix[0][j] = j

    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # deletion
                matrix[i][j - 1] + 1,  # insertion
                matrix[i - 1][j - 1] + cost,  # substitution
            )
    return matrix[len(a)][len(b)]


def simple_replacer(content: str, find: str) -> Generator[str, None, None]:
    """Exact match replacer - yields find string if present in content.

    This is the strictest matcher and preserves backwards compatibility.
    """
    if find in content:
        yield find


def line_trimmed_replacer(content: str, find: str) -> Generator[str, None, None]:
    """Match lines ignoring leading/trailing whitespace per line.

    Compares trimmed versions of each line but yields the original
    content with its actual whitespace preserved.
    """
    original_lines = content.split("\n")
    search_lines = find.split("\n")

    # Remove trailing empty line if present (common from copy-paste)
    if search_lines and search_lines[-1] == "":
        search_lines.pop()

    if not search_lines:
        return

    for i in range(len(original_lines) - len(search_lines) + 1):
        matches = True

        for j in range(len(search_lines)):
            original_trimmed = original_lines[i + j].strip()
            search_trimmed = search_lines[j].strip()

            if original_trimmed != search_trimmed:
                matches = False
                break

        if matches:
            # Calculate the actual substring positions
            match_start_index = 0
            for k in range(i):
                match_start_index += len(original_lines[k]) + 1  # +1 for newline

            match_end_index = match_start_index
            for k in range(len(search_lines)):
                match_end_index += len(original_lines[i + k])
                if k < len(search_lines) - 1:
                    match_end_index += 1  # Add newline except for last line

            yield content[match_start_index:match_end_index]


def indentation_flexible_replacer(content: str, find: str) -> Generator[str, None, None]:
    """Match blocks after normalizing indentation.

    Strips the minimum common indentation from both content blocks
    and find string, then compares. Useful when the LLM gets the
    indentation level wrong but the code structure is correct.
    """

    def remove_indentation(text: str) -> str:
        """Remove common leading indentation from all lines."""
        lines = text.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return text

        # Find minimum indentation
        min_indent = float("inf")
        for line in non_empty_lines:
            stripped = line.lstrip()
            if stripped:
                indent = len(line) - len(stripped)
                min_indent = min(min_indent, indent)

        if min_indent == float("inf") or min_indent == 0:
            return text

        # Remove the common indentation
        result_lines = []
        for line in lines:
            if line.strip():
                result_lines.append(line[int(min_indent) :])
            else:
                result_lines.append(line)

        return "\n".join(result_lines)

    normalized_find = remove_indentation(find)
    content_lines = content.split("\n")
    find_lines = find.split("\n")

    # Remove trailing empty line if present
    if find_lines and find_lines[-1] == "":
        find_lines.pop()

    if not find_lines:
        return

    for i in range(len(content_lines) - len(find_lines) + 1):
        block = "\n".join(content_lines[i : i + len(find_lines)])
        if remove_indentation(block) == normalized_find:
            yield block


def block_anchor_replacer(content: str, find: str) -> Generator[str, None, None]:
    """Match using first/last lines as anchors, fuzzy-match middle.

    This is the fuzziest matcher. It:
    1. Finds blocks where first and last lines match exactly (trimmed)
    2. Uses Levenshtein distance to score middle line similarity
    3. Returns best match if similarity exceeds threshold
    """
    original_lines = content.split("\n")
    search_lines = find.split("\n")

    # Need at least 3 lines for anchor matching to make sense
    if len(search_lines) < 3:
        return

    # Remove trailing empty line if present
    if search_lines[-1] == "":
        search_lines.pop()

    if len(search_lines) < 3:
        return

    first_line_search = search_lines[0].strip()
    last_line_search = search_lines[-1].strip()
    search_block_size = len(search_lines)

    # Collect all candidate positions where both anchors match
    candidates: list[tuple[int, int]] = []
    for i in range(len(original_lines)):
        if original_lines[i].strip() != first_line_search:
            continue

        # Look for matching last line after this first line
        for j in range(i + 2, len(original_lines)):
            if original_lines[j].strip() == last_line_search:
                candidates.append((i, j))
                break  # Only match first occurrence of last line

    if not candidates:
        return

    # Handle single candidate (use relaxed threshold)
    if len(candidates) == 1:
        start_line, end_line = candidates[0]
        actual_block_size = end_line - start_line + 1

        similarity = 0.0
        lines_to_check = min(search_block_size - 2, actual_block_size - 2)

        if lines_to_check > 0:
            for j in range(1, min(search_block_size - 1, actual_block_size - 1)):
                original_line = original_lines[start_line + j].strip()
                search_line = search_lines[j].strip()
                max_len = max(len(original_line), len(search_line))

                if max_len == 0:
                    continue

                distance = levenshtein(original_line, search_line)
                similarity += (1 - distance / max_len) / lines_to_check

                if similarity >= SINGLE_CANDIDATE_SIMILARITY_THRESHOLD:
                    break
        else:
            # No middle lines to compare, accept based on anchors
            similarity = 1.0

        if similarity >= SINGLE_CANDIDATE_SIMILARITY_THRESHOLD:
            match_start_index = sum(len(original_lines[k]) + 1 for k in range(start_line))
            match_end_index = match_start_index
            for k in range(start_line, end_line + 1):
                match_end_index += len(original_lines[k])
                if k < end_line:
                    match_end_index += 1

            yield content[match_start_index:match_end_index]
        return

    # Multiple candidates - find best match
    best_match: tuple[int, int] | None = None
    max_similarity = -1.0

    for start_line, end_line in candidates:
        actual_block_size = end_line - start_line + 1

        similarity = 0.0
        lines_to_check = min(search_block_size - 2, actual_block_size - 2)

        if lines_to_check > 0:
            for j in range(1, min(search_block_size - 1, actual_block_size - 1)):
                original_line = original_lines[start_line + j].strip()
                search_line = search_lines[j].strip()
                max_len = max(len(original_line), len(search_line))

                if max_len == 0:
                    continue

                distance = levenshtein(original_line, search_line)
                similarity += 1 - distance / max_len

            similarity /= lines_to_check  # Average similarity
        else:
            similarity = 1.0

        if similarity > max_similarity:
            max_similarity = similarity
            best_match = (start_line, end_line)

    # Check threshold for multiple candidates
    if max_similarity >= MULTIPLE_CANDIDATES_SIMILARITY_THRESHOLD and best_match:
        start_line, end_line = best_match
        match_start_index = sum(len(original_lines[k]) + 1 for k in range(start_line))
        match_end_index = match_start_index
        for k in range(start_line, end_line + 1):
            match_end_index += len(original_lines[k])
            if k < end_line:
                match_end_index += 1

        yield content[match_start_index:match_end_index]


# Ordered list of replacers from strict to fuzzy
REPLACERS: list[Replacer] = [
    simple_replacer,
    line_trimmed_replacer,
    indentation_flexible_replacer,
    block_anchor_replacer,
]


def replace(content: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """Replace old_string with new_string using fuzzy matching.

    Tries each replacer in order until one succeeds. Replacers are ordered
    from strict (exact match) to fuzzy (anchor-based with Levenshtein).

    Args:
        content: The file content to modify
        old_string: The text to find and replace
        new_string: The replacement text
        replace_all: If True, replace all occurrences; if False, require unique match

    Returns:
        Modified content with replacement applied

    Raises:
        ValueError: If old_string equals new_string
        ValueError: If no match found after trying all strategies
        ValueError: If multiple matches found and replace_all is False
    """
    if old_string == "":
        raise ValueError("old_string cannot be empty; handle file overwrite separately")

    if old_string == new_string:
        raise ValueError("old_string and new_string must be different")

    found_multiple = False

    for replacer in REPLACERS:
        for search in replacer(content, old_string):
            index = content.find(search)
            if index == -1:
                continue

            if replace_all:
                return content.replace(search, new_string)

            # Check for uniqueness - only replace if single occurrence
            last_index = content.rfind(search)
            if index != last_index:
                found_multiple = True
                continue  # Try next replacer for potentially more specific match

            return content[:index] + new_string + content[index + len(search) :]

    if found_multiple:
        raise ValueError(
            "Found multiple matches for old_string. "
            "Provide more surrounding lines in old_string to identify the correct match."
        )

    raise ValueError("old_string not found in content (tried all fuzzy matching strategies)")
