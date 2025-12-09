"""Prompt templates for composing system prompts from sections."""

# Main agent template - default composition order
MAIN_TEMPLATE = """{{AGENT_ROLE}}

====

{{CRITICAL_RULES}}

====

{{TOOL_USE}}

====

{{SEARCH_PATTERN}}

====

{{COMPLETION}}

====

{{PARALLEL_EXEC}}

====

{{OUTPUT_STYLE}}

====

{{EXAMPLES}}

====

{{ADVANCED_PATTERNS}}

====

{{SYSTEM_INFO}}

====

{{USER_INSTRUCTIONS}}"""

# Research agent template - simpler structure focused on exploration
RESEARCH_TEMPLATE = """{{AGENT_ROLE}}

====

{{TOOL_USE}}

====

{{CONSTRAINTS}}

====

{{OUTPUT_FORMAT}}"""

# Model-specific template overrides
# Key: model name prefix (e.g., "gpt-5", "claude-opus")
# Value: custom template string
TEMPLATE_OVERRIDES: dict[str, str] = {
    # Example:
    # "gpt-5": GPT5_TEMPLATE,
    # "claude-opus": OPUS_TEMPLATE,
}
