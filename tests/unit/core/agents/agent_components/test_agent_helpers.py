"""Tests for tunacode.core.agents.agent_components.agent_helpers."""

from tunacode.types.canonical import CanonicalToolCall

from tunacode.core.agents.agent_components.agent_helpers import (
    QUERY_DISPLAY_LIMIT,
    _describe_glob,
    _describe_grep,
    _describe_list_dir,
    _describe_read_file,
    _describe_research,
    create_empty_response_message,
    get_readable_tool_description,
    get_recent_tools_context,
    get_tool_description,
)


class TestDescribeReadFile:
    def test_with_file_path(self):
        assert "main.py" in _describe_read_file({"file_path": "main.py"})

    def test_with_filepath_key(self):
        assert "main.py" in _describe_read_file({"filepath": "main.py"})

    def test_empty(self):
        assert _describe_read_file({}) == "Reading file"


class TestDescribeListDir:
    def test_with_directory(self):
        assert "src/" in _describe_list_dir({"directory": "src/"})

    def test_empty(self):
        assert _describe_list_dir({}) == "Listing directory"


class TestDescribeGrep:
    def test_pattern_and_include(self):
        result = _describe_grep({"pattern": "TODO", "include_files": "*.py"})
        assert "TODO" in result
        assert "*.py" in result

    def test_pattern_only(self):
        result = _describe_grep({"pattern": "TODO"})
        assert "TODO" in result

    def test_empty(self):
        assert _describe_grep({}) == "Searching files"


class TestDescribeGlob:
    def test_with_pattern(self):
        assert "*.py" in _describe_glob({"pattern": "*.py"})

    def test_empty(self):
        assert _describe_glob({}) == "Finding files"


class TestDescribeResearch:
    def test_with_query(self):
        result = _describe_research({"query": "how does auth work"})
        assert "how does auth work" in result

    def test_empty_query(self):
        assert _describe_research({}) == "Researching codebase"

    def test_long_query_truncated(self):
        long_query = "a" * (QUERY_DISPLAY_LIMIT + 20)
        result = _describe_research({"query": long_query})
        assert "..." in result


class TestGetToolDescription:
    def test_grep_with_pattern(self):
        result = get_tool_description("grep", {"pattern": "TODO"})
        assert result == "grep('TODO')"

    def test_glob_with_pattern(self):
        result = get_tool_description("glob", {"pattern": "*.py"})
        assert result == "glob('*.py')"

    def test_read_file_with_path(self):
        result = get_tool_description("read_file", {"file_path": "main.py"})
        assert result == "read_file('main.py')"

    def test_unknown_tool(self):
        assert get_tool_description("bash", {"cmd": "ls"}) == "bash"

    def test_non_dict_args(self):
        assert get_tool_description("bash", "not a dict") == "bash"


class TestGetReadableToolDescription:
    def test_known_tool(self):
        result = get_readable_tool_description("read_file", {"file_path": "x.py"})
        assert "Reading" in result

    def test_unknown_tool(self):
        result = get_readable_tool_description("custom_tool", {"arg": "val"})
        assert result == "Executing `custom_tool`"

    def test_non_dict_args(self):
        result = get_readable_tool_description("bash", "not a dict")
        assert result == "Executing `bash`"


class TestGetRecentToolsContext:
    def test_empty_calls(self):
        assert get_recent_tools_context([]) == "No tools used yet"

    def test_single_call(self):
        calls = [CanonicalToolCall(tool_call_id="1", tool_name="bash", args={"cmd": "ls"})]
        result = get_recent_tools_context(calls)
        assert result == "Recent tools: bash"

    def test_respects_limit(self):
        calls = [
            CanonicalToolCall(tool_call_id=str(i), tool_name=f"tool{i}", args={}) for i in range(10)
        ]
        result = get_recent_tools_context(calls, limit=2)
        assert "tool8" in result
        assert "tool9" in result
        assert "tool0" not in result


class TestCreateEmptyResponseMessage:
    def test_basic_format(self):
        calls = [CanonicalToolCall(tool_call_id="1", tool_name="bash", args={})]
        result = create_empty_response_message("fix the bug", "empty", calls, 1)
        assert "fix the bug" in result
        assert "Attempt: 1" in result
        assert "Recent tools:" in result

    def test_with_no_tool_calls(self):
        result = create_empty_response_message("task", "empty", [], 2)
        assert "No tools used yet" in result
