import json
from pathlib import Path

import streamingjson
from kosong.utils.typing import JsonType


def extract_subtitle(lexer: streamingjson.Lexer, tool_name: str) -> str | None:
    try:
        curr_args: JsonType = json.loads(lexer.complete_json())
    except json.JSONDecodeError:
        return None
    if not curr_args:
        return None
    match tool_name:
        case "Bash":
            if not isinstance(curr_args, dict) or not curr_args.get("command"):
                return None
            return str(curr_args["command"])
        case "Task":
            if not isinstance(curr_args, dict) or not curr_args.get("description"):
                return None
            return str(curr_args["description"])
        case "ReadFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            return _normalize_path(str(curr_args["path"]))
        case "WriteFile":
            if not isinstance(curr_args, dict) or not curr_args.get("path"):
                return None
            return _normalize_path(str(curr_args["path"]))
        case "Glob":
            if not isinstance(curr_args, dict) or not curr_args.get("pattern"):
                return None
            return str(curr_args["pattern"])
        case "Grep":
            if not isinstance(curr_args, dict) or not curr_args.get("pattern"):
                return None
            return str(curr_args["pattern"])
        case _:
            return "".join(lexer.json_content)


def _normalize_path(path: str) -> str:
    cwd = str(Path.cwd().absolute())
    if path.startswith(cwd):
        path = path[len(cwd) :].lstrip("/\\")
    return path
