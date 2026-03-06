from __future__ import annotations

from collections.abc import Iterable

from tunacode.skills.models import SkillSummary

EXACT_NAME_MATCH_RANK = 0
PREFIX_NAME_MATCH_RANK = 1
SUBSTRING_NAME_MATCH_RANK = 2
DESCRIPTION_MATCH_RANK = 3
NO_MATCH = -1
ZERO_MATCH_INDEX = 0

SkillMatchSortKey = tuple[int, int, int, str]


def filter_skill_summaries(
    skill_summaries: Iterable[SkillSummary],
    *,
    query: str | None,
) -> list[SkillSummary]:
    """Return matching skill summaries in deterministic best-match order."""
    if query is None:
        return list(skill_summaries)

    normalized_query = query.casefold().strip()
    if not normalized_query:
        return list(skill_summaries)

    ranked_matches: list[tuple[SkillMatchSortKey, SkillSummary]] = []
    for skill_summary in skill_summaries:
        sort_key = _build_skill_match_sort_key(
            skill_summary=skill_summary,
            normalized_query=normalized_query,
        )
        if sort_key is None:
            continue
        ranked_matches.append((sort_key, skill_summary))

    ranked_matches.sort(key=lambda item: item[0])
    return [skill_summary for _sort_key, skill_summary in ranked_matches]


def _build_skill_match_sort_key(
    *,
    skill_summary: SkillSummary,
    normalized_query: str,
) -> SkillMatchSortKey | None:
    normalized_name = skill_summary.name.casefold()
    normalized_description = skill_summary.description.casefold()
    normalized_name_length = len(normalized_name)

    if normalized_name == normalized_query:
        return (
            EXACT_NAME_MATCH_RANK,
            ZERO_MATCH_INDEX,
            normalized_name_length,
            normalized_name,
        )

    if normalized_name.startswith(normalized_query):
        return (
            PREFIX_NAME_MATCH_RANK,
            ZERO_MATCH_INDEX,
            normalized_name_length,
            normalized_name,
        )

    name_match_index = normalized_name.find(normalized_query)
    if name_match_index != NO_MATCH:
        return (
            SUBSTRING_NAME_MATCH_RANK,
            name_match_index,
            normalized_name_length,
            normalized_name,
        )

    description_match_index = normalized_description.find(normalized_query)
    if description_match_index == NO_MATCH:
        return None

    return (
        DESCRIPTION_MATCH_RANK,
        description_match_index,
        normalized_name_length,
        normalized_name,
    )
