"""Skills command for browsing, searching, and managing loaded skills."""

# ruff: noqa: I001

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rich.text import Text

from tunacode.skills.loader import SkillLoadError
from tunacode.skills.models import SkillSummary
from tunacode.skills.registry import get_skill_summary, list_skill_summaries
from tunacode.skills.search import filter_skill_summaries
from tunacode.skills.selection import (
    attach_skill,
    clear_attached_skills,
    resolve_selected_skill_summaries,
)

from tunacode.ui.commands.base import Command
from tunacode.ui.styles import (
    STYLE_MUTED,
    STYLE_PRIMARY,
    STYLE_SUCCESS,
    STYLE_WARNING,
)
from tunacode.ui.widgets.chat import PanelMeta

if TYPE_CHECKING:
    from tunacode.ui.app import TextualReplApp

SEARCH_SUBCOMMAND_PREFIX = "search "
LOADED_SUBCOMMAND = "loaded"
CLEAR_SUBCOMMAND = "clear"
NO_SOURCE_LABEL = "---"
MISSING_STATUS_LABEL = "missing"
LOADED_STATUS_LABEL = "loaded"
EMPTY_STATE_LABEL = "(none)"
MISSING_SKILL_DESCRIPTION = "Skill file unavailable"
SKILL_PREFIX = "▸ "
SKILL_BULLET_LOADED = "▸"
SKILL_BULLET_AVAILABLE = "○"


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
        panel_title = self._build_available_panel_title(
            query=query,
            match_count=len(matching_skills),
        )

        content = self._build_skills_list_content(
            matching_skills,
            active_skill_names=active_skill_names,
        )

        panel_meta = PanelMeta(
            css_class="info-panel skills-catalog",
            border_title=panel_title,
        )
        app.chat_container.write(content, panel_meta=panel_meta)

    def _render_loaded_skills(self, app: TextualReplApp) -> None:
        loaded_skill_rows = self._build_loaded_skill_rows(app)

        if not loaded_skill_rows:
            content = Text(EMPTY_STATE_LABEL, style=f"dim {STYLE_MUTED}")
            panel_meta = PanelMeta(
                css_class="info-panel skills-loaded",
                border_title="Loaded Skills",
            )
            app.chat_container.write(content, panel_meta=panel_meta)
            return

        content = self._build_loaded_skills_content(loaded_skill_rows)
        panel_meta = PanelMeta(
            css_class="success-panel skills-loaded",
            border_title=f"Loaded Skills [{len(loaded_skill_rows)}]",
        )
        app.chat_container.write(content, panel_meta=panel_meta)

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
            content = self._build_skill_notification_content(summary, status="already-loaded")
            panel_meta = PanelMeta(
                css_class="info-panel skill-notification",
                border_title="Skill",
            )
            app.chat_container.write(content, panel_meta=panel_meta)
            return False

        app.notify(f"Loaded skill: {summary.name}")
        content = self._build_skill_notification_content(summary, status="loaded")
        panel_meta = PanelMeta(
            css_class="success-panel skill-notification",
            border_title="Skill Loaded",
        )
        app.chat_container.write(content, panel_meta=panel_meta)
        return True

    def _clear_loaded_skills(self, app: TextualReplApp) -> None:
        app.state_manager.session.selected_skill_names = clear_attached_skills()
        app._refresh_context_panel()
        app.notify("Cleared loaded skills")
        content = Text("All skills have been removed from the session.", style=STYLE_MUTED)
        panel_meta = PanelMeta(
            css_class="info-panel skill-notification",
            border_title="Skills Cleared",
        )
        app.chat_container.write(content, panel_meta=panel_meta)
        app.chat_container.write("Cleared loaded skills")

    def _build_loaded_skill_rows(self, app: TextualReplApp) -> list[_LoadedSkillRow]:
        loaded_skill_rows: list[_LoadedSkillRow] = []
        resolved_summaries = resolve_selected_skill_summaries(
            app.state_manager.session.selected_skill_names
        )
        for resolved_summary in resolved_summaries:
            summary = resolved_summary.summary
            if summary is None:
                loaded_skill_rows.append(
                    _LoadedSkillRow(
                        name=resolved_summary.requested_name,
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
        return filter_skill_summaries(skill_summaries, query=query)

    def _build_available_panel_title(self, *, query: str | None, match_count: int) -> str:
        if query is None:
            return "Skills Catalog"
        return f"Skills Catalog — {match_count} match(es) for '{query}'"

    def _build_skills_list_content(
        self,
        skill_summaries: list[SkillSummary],
        active_skill_names: set[str],
    ) -> Text:
        content = Text()
        for index, skill_summary in enumerate(skill_summaries):
            is_loaded = skill_summary.name.casefold() in active_skill_names
            bullet = SKILL_BULLET_LOADED if is_loaded else SKILL_BULLET_AVAILABLE
            bullet_style = STYLE_SUCCESS if is_loaded else STYLE_MUTED

            content.append(bullet, style=bullet_style)
            content.append(" ", style=STYLE_MUTED)
            content.append(skill_summary.name, style=STYLE_PRIMARY)
            content.append(f" [{skill_summary.source.value}]", style=f"dim {STYLE_MUTED}")
            if is_loaded:
                content.append(" ✓", style=STYLE_SUCCESS)
            content.append(f"\n  {skill_summary.description}", style=f"dim {STYLE_MUTED}")

            if index < len(skill_summaries) - 1:
                content.append("\n\n")

        return content

    def _build_loaded_skills_content(self, loaded_skill_rows: list[_LoadedSkillRow]) -> Text:
        content = Text()
        for index, row in enumerate(loaded_skill_rows):
            status_bullet = "▸" if row.status_label == LOADED_STATUS_LABEL else "✗"
            status_style = (
                STYLE_SUCCESS if row.status_label == LOADED_STATUS_LABEL else STYLE_WARNING
            )

            content.append(status_bullet, style=status_style)
            content.append(" ", style=STYLE_MUTED)
            content.append(row.name, style=STYLE_PRIMARY)
            if row.source_label != NO_SOURCE_LABEL:
                content.append(f" [{row.source_label}]", style=f"dim {STYLE_MUTED}")
            if row.status_label != LOADED_STATUS_LABEL:
                content.append(f" [{row.status_label}]", style=STYLE_WARNING)
            content.append(f"\n  {row.description}", style=f"dim {STYLE_MUTED}")

            if index < len(loaded_skill_rows) - 1:
                content.append("\n\n")

        return content

    def _build_skill_notification_content(self, summary: SkillSummary, *, status: str) -> Text:
        content = Text()

        if status == "loaded":
            content.append("▸ ", style=STYLE_SUCCESS)
            content.append(summary.name, style=f"bold {STYLE_PRIMARY}")
        else:
            content.append("○ ", style=STYLE_MUTED)
            content.append(summary.name, style=STYLE_PRIMARY)

        content.append(f" [{summary.source.value}]", style=f"dim {STYLE_MUTED}")

        if status == "already-loaded":
            content.append(" (already attached)", style=STYLE_WARNING)

        content.append(f"\n{summary.description}", style=f"dim {STYLE_MUTED}")

        return content
