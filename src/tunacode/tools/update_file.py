"""
Module: tunacode.tools.update_file

File update tool for agent operations in the TunaCode application.
Provides targeted file content modification with diff-based updates.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

import defusedxml.ElementTree as ET
from pydantic_ai.exceptions import ModelRetry

from tunacode.exceptions import ToolExecutionError
from tunacode.tools.base import FileBasedTool
from tunacode.tools.utils.text_match import replace
from tunacode.types import ToolResult

logger = logging.getLogger(__name__)


class UpdateFileTool(FileBasedTool):
    """Tool for updating existing files by replacing text blocks."""

    @property
    def tool_name(self) -> str:
        return "Update"

    @lru_cache(maxsize=1)
    def _get_base_prompt(self) -> str:
        """Load and return the base prompt from XML file.

        Returns:
            str: The loaded prompt from XML or a default prompt
        """
        try:
            # Load prompt from XML file
            prompt_file = Path(__file__).parent / "prompts" / "update_file_prompt.xml"
            if prompt_file.exists():
                tree = ET.parse(prompt_file)
                root = tree.getroot()
                description = root.find("description")
                if description is not None:
                    return description.text.strip()
        except Exception as e:
            logger.warning(f"Failed to load XML prompt for update_file: {e}")

        # Fallback to default prompt
        return """Performs exact string replacements in files"""

    @lru_cache(maxsize=1)
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the parameters schema for update_file tool.

        Returns:
            Dict containing the JSON schema for tool parameters
        """
        # Try to load from XML first
        try:
            prompt_file = Path(__file__).parent / "prompts" / "update_file_prompt.xml"
            if prompt_file.exists():
                tree = ET.parse(prompt_file)
                root = tree.getroot()
                parameters = root.find("parameters")
                if parameters is not None:
                    schema: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}
                    required_fields: List[str] = []

                    for param in parameters.findall("parameter"):
                        name = param.get("name")
                        required = param.get("required", "false").lower() == "true"
                        param_type = param.find("type")
                        description = param.find("description")

                        if name and param_type is not None:
                            prop = {
                                "type": param_type.text.strip(),
                                "description": description.text.strip()
                                if description is not None
                                else "",
                            }

                            schema["properties"][name] = prop
                            if required:
                                required_fields.append(name)

                    schema["required"] = required_fields
                    return schema
        except Exception as e:
            logger.warning(f"Failed to load parameters from XML for update_file: {e}")

        # Fallback to hardcoded schema
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the file to modify",
                },
                "old_string": {
                    "type": "string",
                    "description": "The text to replace",
                },
                "new_string": {
                    "type": "string",
                    "description": "The text to replace it with",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurences of old_string",
                },
            },
            "required": ["file_path", "old_string", "new_string"],
        }

    async def _execute(self, filepath: str, target: str, patch: str) -> ToolResult:
        """Update an existing file by replacing a target text block with a patch.

        Args:
            filepath: The path to the file to update.
            target: The entire, exact block of text to be replaced.
            patch: The new block of text to insert.

        Returns:
            ToolResult: A message indicating success.

        Raises:
            ModelRetry: If file not found or target not found
            Exception: Any file operation errors
        """
        if not os.path.exists(filepath):
            raise ModelRetry(
                f"File '{filepath}' not found. Cannot update. "
                "Verify the filepath or use `write_file` if it's a new file."
            )

        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        try:
            new_content = replace(original, target, patch, replace_all=False)
        except ValueError as e:
            # Provide context to help the LLM understand what went wrong
            error_msg = str(e)
            lines = original.splitlines()
            # For small files, show more context
            preview_lines = min(20, len(lines))
            snippet = "\n".join(lines[:preview_lines])
            raise ModelRetry(
                f"{error_msg}\n\n"
                f"File '{filepath}' preview ({preview_lines} lines):\n---\n{snippet}\n---"
            )

        if original == new_content:
            raise ModelRetry(
                f"Update target found, but replacement resulted in no changes to '{filepath}'. "
                "Was the `target` identical to the `patch`? Please check the file content."
            )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"File '{filepath}' updated successfully."

    def _format_args(self, filepath: str, target: str = None, patch: str = None) -> str:
        """Format arguments, truncating target and patch for display."""
        args = [repr(filepath)]

        if target is not None:
            if len(target) > 50:
                args.append(f"target='{target[:47]}...'")
            else:
                args.append(f"target={repr(target)}")

        if patch is not None:
            if len(patch) > 50:
                args.append(f"patch='{patch[:47]}...'")
            else:
                args.append(f"patch={repr(patch)}")

        return ", ".join(args)


# Create the function that maintains the existing interface
async def update_file(filepath: str, target: str, patch: str) -> str:
    """
    Update an existing file by replacing a target text block with a patch.
    Requires confirmation with diff before applying.

    Args:
        filepath: The path to the file to update.
        target: The entire, exact block of text to be replaced.
        patch: The new block of text to insert.

    Returns:
        str: A message indicating the success or failure of the operation.
    """
    tool = UpdateFileTool(None)  # No UI for pydantic-ai compatibility
    try:
        return await tool.execute(filepath, target, patch)
    except ToolExecutionError as e:
        # Return error message for pydantic-ai compatibility
        return str(e)
