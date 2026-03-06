from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tunacode.skills.models import SkillSource

SKILL_FILE_NAME = "SKILL.md"
LOCAL_SKILLS_ROOT = Path(".claude") / "skills"


class SkillDiscoveryError(RuntimeError):
    """Base exception for skill discovery failures."""


class DuplicateSkillNameError(SkillDiscoveryError):
    """Raised when one root contains duplicate skill names."""


@dataclass(frozen=True, slots=True)
class DiscoveredSkillPath:
    """Filesystem location for a discovered skill."""

    name: str
    source: SkillSource
    skill_dir: Path
    skill_path: Path


@dataclass(frozen=True, slots=True)
class SkillRoot:
    """Resolved skill root with source metadata."""

    source: SkillSource
    path: Path


def resolve_skill_roots(
    *,
    project_root: Path | None = None,
    home_directory: Path | None = None,
) -> tuple[SkillRoot, SkillRoot]:
    """Return project-local and user-global skill roots."""

    resolved_project_root = Path.cwd() if project_root is None else project_root.resolve()
    resolved_home_directory = Path.home() if home_directory is None else home_directory.resolve()

    local_root = SkillRoot(
        source=SkillSource.LOCAL,
        path=(resolved_project_root / LOCAL_SKILLS_ROOT).resolve(),
    )
    global_root = SkillRoot(
        source=SkillSource.GLOBAL,
        path=(resolved_home_directory / ".claude" / "skills").resolve(),
    )
    return local_root, global_root


def discover_skills(
    *,
    local_root: Path | None = None,
    global_root: Path | None = None,
) -> dict[str, DiscoveredSkillPath]:
    """Discover skills with deterministic local-over-global precedence."""

    resolved_local_root, resolved_global_root = _resolve_requested_roots(
        local_root=local_root,
        global_root=global_root,
    )
    discovered_global = _discover_root_skills(resolved_global_root)
    discovered_local = _discover_root_skills(resolved_local_root)
    return _merge_discovered_skills(discovered_global, discovered_local)


def _resolve_requested_roots(
    *,
    local_root: Path | None,
    global_root: Path | None,
) -> tuple[SkillRoot, SkillRoot]:
    if local_root is None and global_root is None:
        return resolve_skill_roots()

    default_local_root, default_global_root = resolve_skill_roots()
    resolved_local_root = (
        default_local_root
        if local_root is None
        else SkillRoot(
            source=SkillSource.LOCAL,
            path=local_root.resolve(),
        )
    )
    resolved_global_root = (
        default_global_root
        if global_root is None
        else SkillRoot(
            source=SkillSource.GLOBAL,
            path=global_root.resolve(),
        )
    )
    return resolved_local_root, resolved_global_root


def _discover_root_skills(root: SkillRoot) -> dict[str, DiscoveredSkillPath]:
    root_path = root.path
    if not root_path.exists():
        return {}

    if not root_path.is_dir():
        raise SkillDiscoveryError(f"Skill root is not a directory: {root_path}")

    discovered_by_name: dict[str, DiscoveredSkillPath] = {}
    discovered_by_key: dict[str, str] = {}

    for child in sorted(root_path.iterdir(), key=lambda entry: entry.name.lower()):
        if not child.is_dir():
            continue

        skill_path = child / SKILL_FILE_NAME
        if not skill_path.is_file():
            continue

        skill_name = child.name
        normalized_name = skill_name.casefold()
        existing_name = discovered_by_key.get(normalized_name)
        if existing_name is not None:
            raise DuplicateSkillNameError(
                f"Duplicate skill names in {root_path}: {existing_name!r} and {skill_name!r}"
            )

        discovered_by_key[normalized_name] = skill_name
        discovered_by_name[skill_name] = DiscoveredSkillPath(
            name=skill_name,
            source=root.source,
            skill_dir=child.resolve(),
            skill_path=skill_path.resolve(),
        )

    return discovered_by_name


def _merge_discovered_skills(
    discovered_global: dict[str, DiscoveredSkillPath],
    discovered_local: dict[str, DiscoveredSkillPath],
) -> dict[str, DiscoveredSkillPath]:
    merged_by_key: dict[str, DiscoveredSkillPath] = {}

    sorted_global_skills = sorted(
        discovered_global.values(),
        key=lambda skill: skill.name.casefold(),
    )
    for discovered_skill in sorted_global_skills:
        merged_by_key[discovered_skill.name.casefold()] = discovered_skill

    sorted_local_skills = sorted(
        discovered_local.values(),
        key=lambda skill: skill.name.casefold(),
    )
    for discovered_skill in sorted_local_skills:
        merged_by_key[discovered_skill.name.casefold()] = discovered_skill

    merged_skills = sorted(merged_by_key.values(), key=lambda skill: skill.name.casefold())
    return {discovered_skill.name: discovered_skill for discovered_skill in merged_skills}
