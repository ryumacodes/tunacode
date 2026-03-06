from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from tunacode.skills.discovery import DiscoveredSkillPath
from tunacode.skills.models import LoadedSkill, SkillSummary

FRONTMATTER_DELIMITER = "---"
FRONTMATTER_REQUIRED_KEYS = ("name", "description")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
MARKDOWN_HEADING_PREFIX = "#"
MARKDOWN_FENCE_PREFIX = "```"
LEGACY_DESCRIPTION_FALLBACK = "Legacy skill"
PATH_SUFFIXES = {
    ".css",
    ".csv",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".js",
    ".json",
    ".md",
    ".pdf",
    ".png",
    ".py",
    ".sh",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".webp",
    ".xml",
    ".yaml",
    ".yml",
}
URL_PREFIXES = ("http://", "https://")
DISALLOWED_REFERENCE_PREFIXES = ("#", "/", "~")
EXCLUDED_RELATED_PATH_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
EXCLUDED_RELATED_FILE_NAMES = {".DS_Store"}
EXCLUDED_RELATED_FILE_SUFFIXES = {".pyc"}


class SkillLoadError(RuntimeError):
    """Base exception for skill loading failures."""


class MissingSkillFileError(SkillLoadError):
    """Raised when a discovered skill path does not exist."""


class SkillFrontmatterError(SkillLoadError):
    """Raised when skill frontmatter is missing or malformed."""


class SkillReferenceError(SkillLoadError):
    """Raised when a referenced relative file is missing."""


class SkillNameMismatchError(SkillLoadError):
    """Raised when the frontmatter name disagrees with the directory name."""


@dataclass(frozen=True, slots=True)
class _ParsedSkillDocument:
    name: str
    description: str
    content: str


def load_skill_summary(discovered_skill: DiscoveredSkillPath) -> SkillSummary:
    """Load startup metadata for a skill without returning the full markdown body."""

    parsed_document = _load_parsed_skill_document(discovered_skill)
    return SkillSummary(
        name=parsed_document.name,
        description=parsed_document.description,
        source=discovered_skill.source,
        skill_dir=discovered_skill.skill_dir,
        skill_path=discovered_skill.skill_path,
    )


def load_skill(discovered_skill: DiscoveredSkillPath) -> LoadedSkill:
    """Load full skill content and validate explicit relative markdown references."""

    parsed_document = _load_parsed_skill_document(discovered_skill)
    referenced_paths = _collect_referenced_paths(
        content=parsed_document.content,
        skill_dir=discovered_skill.skill_dir,
        skill_path=discovered_skill.skill_path,
    )
    return LoadedSkill(
        name=parsed_document.name,
        description=parsed_document.description,
        source=discovered_skill.source,
        skill_dir=discovered_skill.skill_dir,
        skill_path=discovered_skill.skill_path,
        content=parsed_document.content,
        referenced_paths=referenced_paths,
    )


def list_skill_related_paths(skill_dir: Path, *, skill_path: Path) -> tuple[Path, ...]:
    """Return deterministic absolute paths for non-SKILL files under a skill directory."""

    resolved_skill_path = skill_path.resolve()
    related_paths = [
        path.resolve()
        for path in skill_dir.rglob("*")
        if _should_include_related_path(path, resolved_skill_path)
    ]
    return tuple(sorted(set(related_paths), key=lambda path: str(path).casefold()))


def _load_parsed_skill_document(discovered_skill: DiscoveredSkillPath) -> _ParsedSkillDocument:
    raw_content = _read_skill_file(discovered_skill.skill_path)
    if _starts_with_frontmatter(raw_content):
        frontmatter, _body = _parse_frontmatter(raw_content)
        name = _read_required_frontmatter_value(frontmatter, key="name")
        description = _read_required_frontmatter_value(frontmatter, key="description")
        _validate_skill_name(discovered_skill=discovered_skill, name=name)
        return _ParsedSkillDocument(name=name, description=description, content=raw_content)

    description = _derive_legacy_description(raw_content)
    return _ParsedSkillDocument(
        name=discovered_skill.name,
        description=description,
        content=raw_content,
    )


def _read_skill_file(skill_path: Path) -> str:
    try:
        return skill_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise MissingSkillFileError(f"Skill file not found: {skill_path}") from exc


def _starts_with_frontmatter(content: str) -> bool:
    lines = content.splitlines()
    if not lines:
        raise SkillFrontmatterError("Skill file is empty")
    return lines[0].strip() == FRONTMATTER_DELIMITER


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    lines = content.splitlines()
    if not lines:
        raise SkillFrontmatterError("Skill file is empty")

    if lines[0].strip() != FRONTMATTER_DELIMITER:
        raise SkillFrontmatterError("Skill file must begin with YAML frontmatter")

    closing_index = _find_frontmatter_closing_index(lines)
    frontmatter_lines = lines[1:closing_index]
    body_lines = lines[closing_index + 1 :]

    frontmatter: dict[str, str] = {}
    for raw_line in frontmatter_lines:
        stripped_line = raw_line.strip()
        if not stripped_line:
            continue

        if ":" not in stripped_line:
            if raw_line[:1].isspace() and frontmatter:
                continue
            raise SkillFrontmatterError(f"Malformed frontmatter line: {raw_line!r}")

        key, raw_value = stripped_line.split(":", 1)
        normalized_key = key.strip()
        normalized_value = _strip_matching_quotes(raw_value.strip())
        if not normalized_key:
            raise SkillFrontmatterError(f"Malformed frontmatter key: {raw_line!r}")
        frontmatter[normalized_key] = normalized_value

    return frontmatter, "\n".join(body_lines)


def _find_frontmatter_closing_index(lines: list[str]) -> int:
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            return index
    raise SkillFrontmatterError("Skill frontmatter is missing a closing delimiter")


def _strip_matching_quotes(value: str) -> str:
    if len(value) < 2:
        return value

    matching_quote_pairs = (('"', '"'), ("'", "'"))
    for opening_quote, closing_quote in matching_quote_pairs:
        if value.startswith(opening_quote) and value.endswith(closing_quote):
            return value[1:-1]
    return value


def _read_required_frontmatter_value(frontmatter: dict[str, str], *, key: str) -> str:
    value = frontmatter.get(key, "").strip()
    if value:
        return value

    required_keys = ", ".join(FRONTMATTER_REQUIRED_KEYS)
    raise SkillFrontmatterError(
        f"Skill frontmatter must define non-empty keys: {required_keys}; missing {key!r}"
    )


def _validate_skill_name(*, discovered_skill: DiscoveredSkillPath, name: str) -> None:
    if name == discovered_skill.name:
        return

    raise SkillNameMismatchError(
        "Skill frontmatter name does not match directory name: "
        f"expected {discovered_skill.name!r}, got {name!r}"
    )


def _derive_legacy_description(content: str) -> str:
    first_heading: str | None = None
    in_code_fence = False

    for raw_line in content.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line:
            continue

        if stripped_line.startswith(MARKDOWN_FENCE_PREFIX):
            in_code_fence = not in_code_fence
            continue

        if in_code_fence:
            continue

        if stripped_line.startswith(MARKDOWN_HEADING_PREFIX):
            if first_heading is None:
                first_heading = stripped_line.lstrip(MARKDOWN_HEADING_PREFIX).strip()
            continue

        return stripped_line

    if first_heading is not None:
        return first_heading

    return LEGACY_DESCRIPTION_FALLBACK


def _collect_referenced_paths(
    *,
    content: str,
    skill_dir: Path,
    skill_path: Path,
) -> tuple[Path, ...]:
    ordered_paths: list[Path] = []
    seen_paths: set[Path] = set()

    for candidate in _iter_reference_candidates(content):
        relative_reference = _normalize_relative_reference(candidate)
        if relative_reference is None:
            continue

        resolved_path = _resolve_referenced_path(
            relative_reference=relative_reference,
            skill_dir=skill_dir,
            skill_path=skill_path,
        )
        if resolved_path in seen_paths:
            continue

        ordered_paths.append(resolved_path)
        seen_paths.add(resolved_path)

    return tuple(ordered_paths)


def _resolve_referenced_path(
    *,
    relative_reference: str,
    skill_dir: Path,
    skill_path: Path,
) -> Path:
    direct_path = (skill_dir / relative_reference).resolve()
    if direct_path.exists():
        return direct_path

    reference_parts = Path(relative_reference).parts
    if len(reference_parts) > 1:
        raise SkillReferenceError(
            f"Skill {skill_path} references missing relative path: {relative_reference}"
        )

    matching_paths = _find_recursive_reference_matches(skill_dir, reference_parts[0])
    if not matching_paths:
        raise SkillReferenceError(
            f"Skill {skill_path} references missing relative path: {relative_reference}"
        )

    if len(matching_paths) > 1:
        raise SkillReferenceError(
            f"Skill {skill_path} references ambiguous relative path: {relative_reference}"
        )

    return matching_paths[0]


def _find_recursive_reference_matches(skill_dir: Path, file_name: str) -> list[Path]:
    matching_paths = [path.resolve() for path in skill_dir.rglob(file_name) if path.is_file()]
    return sorted(set(matching_paths))


def _should_include_related_path(path: Path, skill_path: Path) -> bool:
    if not path.is_file():
        return False

    resolved_path = path.resolve()
    if resolved_path == skill_path:
        return False

    if resolved_path.name in EXCLUDED_RELATED_FILE_NAMES:
        return False

    if resolved_path.suffix.lower() in EXCLUDED_RELATED_FILE_SUFFIXES:
        return False

    return not any(part in EXCLUDED_RELATED_PATH_PARTS for part in resolved_path.parts)


def _iter_reference_candidates(content: str) -> list[str]:
    candidates: list[str] = []
    for match in MARKDOWN_LINK_PATTERN.finditer(content):
        candidates.append(match.group(1))
    return candidates


def _normalize_relative_reference(raw_reference: str) -> str | None:
    reference = raw_reference.strip()
    if not reference:
        return None
    if reference.startswith(URL_PREFIXES):
        return None
    if reference.startswith(DISALLOWED_REFERENCE_PREFIXES):
        return None
    if "://" in reference:
        return None
    if " " in reference:
        return None

    anchor_trimmed_reference = reference.split("#", 1)[0]
    query_trimmed_reference = anchor_trimmed_reference.split("?", 1)[0]
    if not query_trimmed_reference:
        return None

    candidate_path = Path(query_trimmed_reference)
    suffix = candidate_path.suffix.lower()
    if suffix in PATH_SUFFIXES:
        return query_trimmed_reference
    if query_trimmed_reference.endswith("/"):
        return query_trimmed_reference.rstrip("/")
    return None
