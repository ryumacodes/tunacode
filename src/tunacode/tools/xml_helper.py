"""Helper module for loading prompts and schemas from XML files."""

from __future__ import annotations

from pathlib import Path

from defusedxml.ElementTree import ParseError
from defusedxml.ElementTree import parse as xml_parse

from tunacode.tools.cache_accessors import xml_prompts_cache


def load_prompt_from_xml(tool_name: str) -> str | None:
    """Load and return the base prompt from XML file.

    Args:
        tool_name: Name of the tool (e.g., 'grep', 'glob')

    Returns:
        The loaded prompt from XML or None if not found.
    """

    cache_hit, cached = xml_prompts_cache.try_get_prompt(tool_name)
    if cache_hit:
        return cached

    prompt_file = Path(__file__).parent / "prompts" / f"{tool_name}_prompt.xml"
    if not prompt_file.exists():
        xml_prompts_cache.set_prompt(tool_name, prompt=None, file_path=prompt_file)
        return None

    try:
        tree = xml_parse(prompt_file)
    except ParseError:
        xml_prompts_cache.set_prompt(tool_name, prompt=None, file_path=prompt_file)
        return None

    root = tree.getroot()
    description = root.find("description")
    if description is None or description.text is None:
        xml_prompts_cache.set_prompt(tool_name, prompt=None, file_path=prompt_file)
        return None

    prompt = description.text.strip()
    xml_prompts_cache.set_prompt(tool_name, prompt=prompt, file_path=prompt_file)
    return prompt
