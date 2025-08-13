"""Test for prompt injection system - Phase 5."""

import json

from tunacode.tools.glob import GlobTool
from tunacode.tools.grep import ParallelGrep
from tunacode.tools.schema_assembler import ToolSchemaAssembler


class TestPromptInjection:
    """Test that prompts are dynamically injected when sent to the API."""

    def test_prompt_loaded_from_xml(self):
        """Test that tools load prompts from XML files."""
        # Create grep tool
        grep_tool = ParallelGrep()

        # Check that prompt was loaded from XML
        prompt = grep_tool._get_base_prompt()
        assert "powerful search tool built on ripgrep" in prompt.lower()
        assert "Usage:" in prompt
        assert "ALWAYS use Grep for search tasks" in prompt

        # Create glob tool
        glob_tool = GlobTool()

        # Check that prompt was loaded from XML
        prompt = glob_tool._get_base_prompt()
        assert "file pattern matching tool" in prompt.lower()
        assert "Supports glob patterns" in prompt

    def test_schema_includes_dynamic_prompt(self):
        """Test that tool schema includes the dynamically loaded prompt."""
        # Create grep tool
        grep_tool = ParallelGrep()

        # Get the tool schema (this is what would be sent to the API)
        schema = grep_tool.get_tool_schema()

        # Verify schema structure
        assert schema["name"] == "grep"
        assert "description" in schema
        assert "parameters" in schema

        # Verify the description contains the XML-loaded prompt
        description = schema["description"]
        assert "powerful search tool built on ripgrep" in description.lower()
        assert "ALWAYS use Grep for search tasks" in description

        # Verify parameters were loaded from XML
        params = schema["parameters"]
        assert params["type"] == "object"
        assert "pattern" in params["properties"]
        assert "pattern" in params["required"]
        assert (
            params["properties"]["pattern"]["description"]
            == "The regular expression pattern to search for in file contents"
        )

    def test_schema_assembler_integration(self):
        """Test that the schema assembler correctly integrates tool prompts."""
        # Create schema assembler
        assembler = ToolSchemaAssembler()

        # Register tools
        assembler.register_tool(ParallelGrep())
        assembler.register_tool(GlobTool())

        # Get all schemas (simulating API call preparation)
        schemas = assembler.get_all_schemas()

        # Verify we have both tools
        assert len(schemas) == 2
        tool_names = {schema["name"] for schema in schemas}
        assert "grep" in tool_names
        assert "glob" in tool_names

        # Find grep schema and verify it has the XML prompt
        grep_schema = next(s for s in schemas if s["name"] == "grep")
        assert "powerful search tool built on ripgrep" in grep_schema["description"].lower()

        # Find glob schema and verify it has the XML prompt
        glob_schema = next(s for s in schemas if s["name"] == "glob")
        assert "file pattern matching tool" in glob_schema["description"].lower()

    def test_api_call_format(self):
        """Test that schemas are formatted correctly for API calls."""
        # Create grep tool
        grep_tool = ParallelGrep()

        # Get schema as it would be sent to API
        schema = grep_tool.get_tool_schema()

        # Verify it's JSON-serializable (required for API calls)
        json_str = json.dumps(schema)
        assert json_str

        # Verify the structure matches OpenAI function calling format
        assert isinstance(schema, dict)
        assert isinstance(schema["name"], str)
        assert isinstance(schema["description"], str)
        assert isinstance(schema["parameters"], dict)
        assert schema["parameters"]["type"] == "object"
        assert isinstance(schema["parameters"]["properties"], dict)
        assert isinstance(schema["parameters"]["required"], list)

    def test_prompt_updates_dynamically(self):
        """Test that prompts can be updated dynamically without code changes."""
        # Create grep tool
        grep_tool = ParallelGrep()

        # Get initial prompt
        initial_prompt = grep_tool._get_base_prompt()
        assert initial_prompt

        # Simulate XML file change by modifying the base prompt method
        grep_tool._get_base_prompt = lambda: "Updated prompt from modified XML"

        # Get schema with updated prompt
        schema = grep_tool.get_tool_schema()
        assert schema["description"] == "Updated prompt from modified XML"

        # This demonstrates that prompts can be updated by modifying XML files
        # without changing any Python code
