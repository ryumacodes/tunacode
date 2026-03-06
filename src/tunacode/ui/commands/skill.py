"""Skill command for listing and managing attached skills."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tunacode.ui.commands.base import Command
from tunacode.ui.styles import STYLE_PRIMARY

from tunacode.skills.registry import list_skill_summaries
from tunacode.skills.selection import attach_skill, clear_attached_skills

if TYPE_CHECKING:
    from tunacode.ui.app import TextualReplApp


class SkillCommand(Command):
    """List available skills and manage the active skill attachments."""

    name = "skill"
    description = "List, attach, or clear session skills"
    usage = "/skill [name|clear]"

    async def execute(self, app: TextualReplApp, args: str) -> None:
        requested_argument = args.strip()
        if not requested_argument:
            self._render_available_skills(app)
            return

        if requested_argument == "clear":
            self._clear_attached_skills(app)
            await app.state_manager.save_session()
            return

        selection_changed = self._attach_skill(app, requested_argument)
        if selection_changed:
            await app.state_manager.save_session()

    def _render_available_skills(self, app: TextualReplApp) -> None:
        from rich.table import Table

        available_skills = list_skill_summaries()
        if not available_skills:
            app.notify("No skills found")
            return

        active_skill_names = {
            skill_name.casefold() for skill_name in app.state_manager.session.selected_skill_names
        }
        table = Table(title="Available Skills", show_header=True)
        table.add_column("Name", style=STYLE_PRIMARY)
        table.add_column("Source")
        table.add_column("Active")
        table.add_column("Description")

        for skill_summary in available_skills:
            is_active = "yes" if skill_summary.name.casefold() in active_skill_names else ""
            table.add_row(
                skill_summary.name,
                skill_summary.source.value,
                is_active,
                skill_summary.description,
            )

        app.chat_container.write(table)

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

        session.selected_skill_names = next_skill_names
        app._refresh_context_panel()
        if already_attached:
            app.notify(f"Skill already attached: {summary.name}")
            app.chat_container.write(
                f"Skill already attached: {summary.name} [{summary.source.value}]"
            )
            return False

        app.notify(f"Attached skill: {summary.name}")
        app.chat_container.write(f"Attached skill: {summary.name} [{summary.source.value}]")
        return True

    def _clear_attached_skills(self, app: TextualReplApp) -> None:
        app.state_manager.session.selected_skill_names = clear_attached_skills()
        app._refresh_context_panel()
        app.notify("Cleared attached skills")
        app.chat_container.write("Cleared attached skills")
