"""Textual widgets for TunaCode REPL."""

from __future__ import annotations

import importlib
from typing import Any

_WIDGET_EXPORTS = {
    "ChatContainer": ".chat",
    "PanelMeta": ".chat",
    "CommandAutoComplete": ".command_autocomplete",
    "Editor": ".editor",
    "FileAutoComplete": ".file_autocomplete",
    "EditorCompletionsAvailable": ".messages",
    "EditorSubmitRequested": ".messages",
    "ToolResultDisplay": ".messages",
    "TuiLogDisplay": ".messages",
    "SystemNoticeDisplay": ".messages",
    "CompactionStatusChanged": ".messages",
    "ResourceBar": ".resource_bar",
    "SkillsAutoComplete": ".skills_autocomplete",
}


def __getattr__(name: str) -> Any:
    module_name = _WIDGET_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(importlib.import_module(module_name, __name__), name)
