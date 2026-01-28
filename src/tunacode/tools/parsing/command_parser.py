"""Module: tunacode.cli.command_parser

Command parsing utilities for the Textual REPL."""

import json
from typing import Any

from tunacode.exceptions import ValidationError

from tunacode.tools.parsing.json_utils import safe_json_parse
from tunacode.tools.parsing.retry import retry_json_parse_async

JSON_PARSE_MAX_RETRIES = 10
JSON_PARSE_BASE_DELAY = 0.1
JSON_PARSE_MAX_DELAY = 5.0


async def parse_args(args: Any) -> dict[str, Any]:
    """
    Parse tool arguments from a JSON string or dictionary with retry logic.

    Args:
        args (str or dict): A JSON-formatted string or a dictionary containing tool arguments.

    Returns:
        dict: The parsed arguments.

    Raises:
        ValidationError: If 'args' is not a string or dictionary, or if the string
        is not valid JSON.
    """
    if isinstance(args, str):
        try:
            return await retry_json_parse_async(
                args,
                max_retries=JSON_PARSE_MAX_RETRIES,
                base_delay=JSON_PARSE_BASE_DELAY,
                max_delay=JSON_PARSE_MAX_DELAY,
            )
        except json.JSONDecodeError as e:
            if "Extra data" in str(e):
                try:
                    result = safe_json_parse(args, allow_concatenated=True)
                    if isinstance(result, dict):
                        return result
                    elif isinstance(result, list) and result:
                        return result[0]
                except Exception:
                    pass

            raise ValidationError(f"Invalid JSON: {args}") from e
    elif isinstance(args, dict):
        return args
    else:
        raise ValidationError(f"Invalid args type: {type(args)}")
