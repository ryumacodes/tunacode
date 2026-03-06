"""Skills command for browsing, searching, and managing loaded skills."""

# ruff: noqa: I001

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tunacode.skills.loader import SkillLoadError
from tunacode.skills.models import SkillSummary
from tunacode.skills.registry import get_skill_summary, list_skill_summaries
from tunacode.skills.selection import attach_skill, clear_attached_skills

from tunacode.ui.commands.base import Command
from tunacode.ui.styles import STYLE_PRIMARY, STYLE_SUCCESS, STYLE_WARNING

if TYPE_CHECKING:
    from tunacode.ui.app import TextualReplApp

SEARCH_SUBCOMMAND_PREFIX = "search "
LOADED_SUBCOMMAND = "loaded"
CLEAR_SUBCOMMAND = "clear"
NO_SOURCE_LABEL = "---"
MISSING_STATUS_LABEL = "missing"
LOADED_STATUS_LABEL = "loaded"
UNIQUE_MATCH_LABEL = "yes"
EMPTY_STATE_LABEL = "(none)"
MISSING_SKILL_DESCRIPTION = "Skill file unavailable"


@dataclass(frozen=True, slots=True)
class _LoadedSkillRow:
    name: str
    source_label: str
    status_label: str
    description: str


class SkillsCommand(Command):
    """Browse the skill catalog and manage loaded session skills."""

    name = "skills"
    description = "Browse, search, and load session skills"
    usage = "/skills [loaded|clear|search <query>|<exact-name>]"

    async def execute(self, app: TextualReplApp, args: str) -> None:
        requested_argument = args.strip()
        if not requested_argument:
            self._render_available_skills(app)
            return

        normalized_argument = requested_argument.casefold()
        if normalized_argument == LOADED_SUBCOMMAND:
            self._render_loaded_skills(app)
            return

        if normalized_argument == CLEAR_SUBCOMMAND:
            self._clear_loaded_skills(app)
            await app.state_manager.save_session()
            return

        if normalized_argument.startswith(SEARCH_SUBCOMMAND_PREFIX):
            search_query = requested_argument[len(SEARCH_SUBCOMMAND_PREFIX) :].strip()
            if not search_query:
                app.notify("Usage: /skills search <query>", severity="warning")
                return
            self._render_available_skills(app, query=search_query)
            return

        selection_changed = self._attach_or_search_skill(app, requested_argument)
        if selection_changed:
            await app.state_manager.save_session()

    def _render_available_skills(self, app: TextualReplApp, *, query: str | None = None) -> None:
        from rich.table import Table

        available_skills = list_skill_summaries()
        if not available_skills:
            app.notify("No skills found")
            return

        matching_skills = self._filter_skill_summaries(available_skills, query=query)
        if not matching_skills:
            app.notify(f"No skills match: {query}", severity="warning")
            return

        active_skill_names = {
            skill_name.casefold() for skill_name in app.state_manager.session.selected_skill_names
        }
        table_title = self._build_available_table_title(
            query=query,
            match_count=len(matching_skills),
        )
        table = Table(title=table_title, show_header=True)
        table.add_column("Name", style=STYLE_PRIMARY)
        table.add_column("Source")
        table.add_column("Loaded")
        table.add_column("Description")

        for skill_summary in matching_skills:
            loaded_label = (
                UNIQUE_MATCH_LABEL if skill_summary.name.casefold() in active_skill_names else ""
            )
            table.add_row(
                skill_summary.name,
                skill_summary.source.value,
                loaded_label,
                skill_summary.description,
            )

        app.chat_container.write(table)

    def _render_loaded_skills(self, app: TextualReplApp) -> None:
        from rich.table import Table

        loaded_skill_rows = self._build_loaded_skill_rows(app)
        table = Table(title="Loaded Skills", show_header=True)
        table.add_column("Name", style=STYLE_PRIMARY)
        table.add_column("Source")
        table.add_column("Status")
        table.add_column("Description")

        if not loaded_skill_rows:
            table.add_row(EMPTY_STATE_LABEL, NO_SOURCE_LABEL, EMPTY_STATE_LABEL, EMPTY_STATE_LABEL)
            app.chat_container.write(table)
            return

        for loaded_skill_row in loaded_skill_rows:
            status_style = self._status_style(loaded_skill_row.status_label)
            table.add_row(
                loaded_skill_row.name,
                loaded_skill_row.source_label,
                f"[{status_style}]{loaded_skill_row.status_label}[/{status_style}]",
                loaded_skill_row.description,
            )

        app.chat_container.write(table)

    def _attach_or_search_skill(self, app: TextualReplApp, requested_name: str) -> bool:
        requested_summary = get_skill_summary(requested_name)
        if requested_summary is None:
            self._render_available_skills(app, query=requested_name)
            app.notify(
                f"No exact skill named: {requested_name}. Showing matches.",
                severity="warning",
            )
            return False

        return self._attach_skill(app, requested_summary.name)

    def _attach_skill(self, app: TextualReplApp, requested_name: str) -> bool:
        session = app.state_manager.session

        try:
            next_skill_names, summary, already_attached = attach_skill(
                session.selected_skill_names,
                requested_name,
            )
        except KeyError:
            app.notify(f"Unknown skill: {requested_name}", severity="error")
            return False
        except SkillLoadError as exc:
            app.notify(f"Failed to load skill: {requested_name}", severity="error")
            app.chat_container.write(f"Failed to load skill: {requested_name} ({exc})")
            return False

        session.selected_skill_names = next_skill_names
        app._refresh_context_panel()
        if already_attached:
            app.notify(f"Skill already loaded: {summary.name}")
            app.chat_container.write(
                f"Skill already loaded: {summary.name} [{summary.source.value}]"
            )
            return False

        app.notify(f"Loaded skill: {summary.name}")
        app.chat_container.write(f"Loaded skill: {summary.name} [{summary.source.value}]")
        return True

    def _clear_loaded_skills(self, app: TextualReplApp) -> None:
        app.state_manager.session.selected_skill_names = clear_attached_skills()
        app._refresh_context_panel()
        app.notify("Cleared loaded skills")
        app.chat_container.write("Cleared loaded skills")

    def _build_loaded_skill_rows(self, app: TextualReplApp) -> list[_LoadedSkillRow]:
        loaded_skill_rows: list[_LoadedSkillRow] = []
        for loaded_skill_name in app.state_manager.session.selected_skill_names:
            summary = get_skill_summary(loaded_skill_name)
            if summary is None:
                loaded_skill_rows.append(
                    _LoadedSkillRow(
                        name=loaded_skill_name,
                        source_label=NO_SOURCE_LABEL,
                        status_label=MISSING_STATUS_LABEL,
                        description=MISSING_SKILL_DESCRIPTION,
                    )
                )
                continue

            loaded_skill_rows.append(
                _LoadedSkillRow(
                    name=summary.name,
                    source_label=summary.source.value,
                    status_label=LOADED_STATUS_LABEL,
                    description=summary.description,
                )
            )

        return loaded_skill_rows

    def _filter_skill_summaries(
        self,
        skill_summaries: list[SkillSummary],
        *,
        query: str | None,
    ) -> list[SkillSummary]:
        if query is None:
            return skill_summaries

        normalized_query = query.casefold()
        matching_skills: list[SkillSummary] = []
        for skill_summary in skill_summaries:
            if normalized_query in skill_summary.name.casefold():
                matching_skills.append(skill_summary)
                continue

            if normalized_query in skill_summary.description.casefold():
                matching_skills.append(skill_summary)

        return matching_skills

    def _build_available_table_title(self, *, query: str | None, match_count: int) -> str:
        if query is None:
            return "Skills Catalog"
        return f"Skills Catalog — {match_count} match(es) for '{query}'"

    def _status_style(self, status_label: str) -> str:
        if status_label == LOADED_STATUS_LABEL:
            return STYLE_SUCCESS
        return STYLE_WARNING
