"""Deep coverage tests for renderer modules.

Targets missed lines in:
- search.py: SearchDisplayRenderer render methods (render_file_results,
  render_code_results, render_inline_results, render_empty_results),
  file_search_panel, code_search_panel, quick_results
- panels.py: RichPanelRenderer static methods (render_tool, render_diff_tool,
  render_error, render_search_results, render_info, render_success,
  render_warning), tool_panel, error_panel, search_panel, tool_panel_smart
- errors.py: render_tool_error deep paths, render_validation_error,
  render_user_abort, render_catastrophic_error, render_exception,
  render_connection_error
"""

from __future__ import annotations

from datetime import datetime

from rich.panel import Panel
from rich.text import Text

from tunacode.ui.renderers.errors import (
    render_catastrophic_error,
    render_connection_error,
    render_exception,
    render_tool_error,
    render_user_abort,
    render_validation_error,
)
from tunacode.ui.renderers.panels import (
    ErrorDisplayData,
    RichPanelRenderer,
    SearchResultData,
    ToolDisplayData,
    error_panel,
    search_panel,
    tool_panel,
    tool_panel_smart,
)
from tunacode.ui.renderers.search import (
    CodeSearchResult,
    FileSearchResult,
    SearchDisplayRenderer,
    code_search_panel,
    file_search_panel,
    quick_results,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_LINE_WIDTH = 80


# ===================================================================
# search.py — SearchDisplayRenderer render methods
# ===================================================================


class TestRenderFileResults:
    """SearchDisplayRenderer.render_file_results builds a rich panel."""

    def test_single_result_without_match_positions(self) -> None:
        results = [
            FileSearchResult(file_path="src/main.py", line_number=10, content="hello world"),
        ]
        panel = SearchDisplayRenderer.render_file_results("hello", results)
        assert panel is not None

    def test_single_result_with_match_positions(self) -> None:
        results = [
            FileSearchResult(
                file_path="src/main.py",
                line_number=5,
                content="say hello there",
                match_start=4,
                match_end=9,
            ),
        ]
        panel = SearchDisplayRenderer.render_file_results("hello", results)
        assert panel is not None

    def test_result_without_line_number(self) -> None:
        results = [
            FileSearchResult(file_path="README.md", content="some content"),
        ]
        panel = SearchDisplayRenderer.render_file_results("content", results)
        assert panel is not None

    def test_result_with_relevance_score(self) -> None:
        results = [
            FileSearchResult(
                file_path="lib.py",
                line_number=1,
                content="match",
                relevance=0.95,
            ),
        ]
        panel = SearchDisplayRenderer.render_file_results("match", results)
        assert panel is not None

    def test_multiple_results_with_pagination(self) -> None:
        results = [
            FileSearchResult(file_path=f"file{i}.py", line_number=i, content=f"line {i}")
            for i in range(25)
        ]
        panel = SearchDisplayRenderer.render_file_results("line", results, page=2, page_size=5)
        assert panel is not None

    def test_with_search_time(self) -> None:
        results = [
            FileSearchResult(file_path="a.py", line_number=1, content="x"),
        ]
        panel = SearchDisplayRenderer.render_file_results(
            "x", results, search_time_ms=42.5
        )
        assert panel is not None

    def test_empty_results_list(self) -> None:
        panel = SearchDisplayRenderer.render_file_results("missing", [])
        assert panel is not None


class TestRenderCodeResults:
    """SearchDisplayRenderer.render_code_results builds a rich panel."""

    def test_single_function_result(self) -> None:
        results = [
            CodeSearchResult(
                file_path="src/core.py",
                symbol_name="process",
                symbol_type="function",
                line_number=42,
                context="def process(data):",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("process", results)
        assert panel is not None

    def test_class_result(self) -> None:
        results = [
            CodeSearchResult(
                file_path="models.py",
                symbol_name="User",
                symbol_type="class",
                line_number=1,
                context="class User:",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("User", results)
        assert panel is not None

    def test_variable_result(self) -> None:
        results = [
            CodeSearchResult(
                file_path="config.py",
                symbol_name="MAX_SIZE",
                symbol_type="variable",
                line_number=3,
                context="MAX_SIZE = 100",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("MAX_SIZE", results)
        assert panel is not None

    def test_method_result(self) -> None:
        results = [
            CodeSearchResult(
                file_path="app.py",
                symbol_name="run",
                symbol_type="method",
                line_number=10,
                context="def run(self):",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("run", results)
        assert panel is not None

    def test_constant_result(self) -> None:
        results = [
            CodeSearchResult(
                file_path="const.py",
                symbol_name="PI",
                symbol_type="constant",
                line_number=1,
                context="PI = 3.14159",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("PI", results)
        assert panel is not None

    def test_unknown_symbol_type_uses_prefix(self) -> None:
        results = [
            CodeSearchResult(
                file_path="x.py",
                symbol_name="thing",
                symbol_type="namespace",
                line_number=1,
                context="namespace thing {}",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("thing", results)
        assert panel is not None

    def test_with_relevance(self) -> None:
        results = [
            CodeSearchResult(
                file_path="a.py",
                symbol_name="foo",
                symbol_type="function",
                line_number=1,
                context="def foo():",
                relevance=0.8,
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results("foo", results)
        assert panel is not None

    def test_pagination(self) -> None:
        results = [
            CodeSearchResult(
                file_path=f"f{i}.py",
                symbol_name=f"func{i}",
                symbol_type="function",
                line_number=i,
                context=f"def func{i}():",
            )
            for i in range(20)
        ]
        panel = SearchDisplayRenderer.render_code_results(
            "func", results, page=2, page_size=5
        )
        assert panel is not None

    def test_with_search_time(self) -> None:
        results = [
            CodeSearchResult(
                file_path="b.py",
                symbol_name="bar",
                symbol_type="function",
                line_number=1,
                context="def bar():",
            ),
        ]
        panel = SearchDisplayRenderer.render_code_results(
            "bar", results, search_time_ms=15.3
        )
        assert panel is not None


class TestRenderInlineResults:
    """SearchDisplayRenderer.render_inline_results returns Text."""

    def test_empty_results_returns_no_results_text(self) -> None:
        result = SearchDisplayRenderer.render_inline_results([])
        assert isinstance(result, Text)

    def test_single_result(self) -> None:
        results = [{"title": "src/main.py"}]
        result = SearchDisplayRenderer.render_inline_results(results)
        assert result is not None

    def test_results_with_file_key_fallback(self) -> None:
        results = [{"file": "src/main.py"}]
        result = SearchDisplayRenderer.render_inline_results(results)
        assert result is not None

    def test_results_with_neither_title_nor_file(self) -> None:
        results = [{"name": "something"}]
        result = SearchDisplayRenderer.render_inline_results(results)
        assert result is not None

    def test_more_than_max_display_shows_remaining(self) -> None:
        results = [{"title": f"file{i}.py"} for i in range(10)]
        result = SearchDisplayRenderer.render_inline_results(results, max_display=3)
        assert result is not None

    def test_exact_max_display_no_remaining(self) -> None:
        results = [{"title": f"file{i}.py"} for i in range(5)]
        result = SearchDisplayRenderer.render_inline_results(results, max_display=5)
        assert result is not None


class TestRenderEmptyResults:
    """SearchDisplayRenderer.render_empty_results returns a Panel."""

    def test_returns_panel(self) -> None:
        result = SearchDisplayRenderer.render_empty_results("nonexistent")
        assert isinstance(result, Panel)

    def test_panel_title_contains_no_results(self) -> None:
        result = SearchDisplayRenderer.render_empty_results("foo")
        assert isinstance(result, Panel)
        title_str = str(result.title) if result.title else ""
        assert "No Results" in title_str


# ===================================================================
# search.py — module-level convenience functions
# ===================================================================


class TestFileSearchPanel:
    """file_search_panel routes to render methods."""

    def test_empty_results_shows_empty_panel(self) -> None:
        result = file_search_panel("query", [])
        assert isinstance(result, Panel)

    def test_with_results(self) -> None:
        results = [
            FileSearchResult(file_path="a.py", line_number=1, content="x"),
        ]
        result = file_search_panel("x", results)
        assert result is not None

    def test_with_page_and_time(self) -> None:
        results = [
            FileSearchResult(file_path="a.py", line_number=1, content="x"),
        ]
        result = file_search_panel("x", results, page=1, search_time_ms=10.0)
        assert result is not None


class TestCodeSearchPanel:
    """code_search_panel routes to render methods."""

    def test_empty_results_shows_empty_panel(self) -> None:
        result = code_search_panel("query", [])
        assert isinstance(result, Panel)

    def test_with_results(self) -> None:
        results = [
            CodeSearchResult(
                file_path="a.py",
                symbol_name="func",
                symbol_type="function",
                line_number=1,
                context="def func():",
            ),
        ]
        result = code_search_panel("func", results)
        assert result is not None

    def test_with_page_and_time(self) -> None:
        results = [
            CodeSearchResult(
                file_path="a.py",
                symbol_name="func",
                symbol_type="function",
                line_number=1,
                context="def func():",
            ),
        ]
        result = code_search_panel("func", results, page=1, search_time_ms=5.0)
        assert result is not None


class TestQuickResults:
    """quick_results convenience function."""

    def test_empty_list(self) -> None:
        result = quick_results([])
        assert isinstance(result, Text)

    def test_with_items(self) -> None:
        result = quick_results([{"title": "a"}, {"title": "b"}])
        assert result is not None

    def test_custom_max_display(self) -> None:
        results = [{"title": f"item{i}"} for i in range(10)]
        result = quick_results(results, max_display=2)
        assert result is not None


# ===================================================================
# panels.py — RichPanelRenderer static methods
# ===================================================================


class TestRichPanelRendererTool:
    """RichPanelRenderer.render_tool builds tool panels."""

    def test_running_status(self) -> None:
        data = ToolDisplayData(
            tool_name="bash",
            status="running",
            arguments={"command": "ls -la"},
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_completed_status(self) -> None:
        data = ToolDisplayData(
            tool_name="read_file",
            status="completed",
            arguments={"path": "/tmp/test.py"},
            result="file contents here",
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_failed_status(self) -> None:
        data = ToolDisplayData(
            tool_name="write_file",
            status="failed",
            arguments={"path": "/readonly.txt"},
            result="Permission denied",
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_unknown_status_uses_info(self) -> None:
        data = ToolDisplayData(
            tool_name="custom",
            status="pending",
            arguments={},
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_with_duration(self) -> None:
        data = ToolDisplayData(
            tool_name="bash",
            status="completed",
            arguments={"command": "echo hi"},
            duration_ms=123.4,
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_with_timestamp(self) -> None:
        data = ToolDisplayData(
            tool_name="bash",
            status="completed",
            arguments={},
            timestamp=datetime(2025, 1, 15, 10, 30, 45),
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)
        assert result.subtitle is not None

    def test_empty_arguments_and_no_result(self) -> None:
        data = ToolDisplayData(
            tool_name="noop",
            status="running",
            arguments={},
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_long_result_triggers_truncation(self) -> None:
        long_result = "\n".join(f"line {i}" for i in range(200))
        data = ToolDisplayData(
            tool_name="bash",
            status="completed",
            arguments={"command": "generate_output"},
            result=long_result,
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)

    def test_multiple_arguments(self) -> None:
        data = ToolDisplayData(
            tool_name="grep",
            status="completed",
            arguments={"pattern": "test", "path": "/src", "recursive": True},
            result="found 3 matches",
        )
        result = RichPanelRenderer.render_tool(data, max_line_width=DEFAULT_MAX_LINE_WIDTH)
        assert isinstance(result, Panel)


class TestRichPanelRendererDiffTool:
    """RichPanelRenderer.render_diff_tool builds diff panels."""

    def test_basic_diff(self) -> None:
        diff = "--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new"
        result = RichPanelRenderer.render_diff_tool(
            tool_name="update_file",
            message="Updated file.py",
            diff=diff,
        )
        assert isinstance(result, Panel)

    def test_with_args(self) -> None:
        diff = "-old\n+new"
        result = RichPanelRenderer.render_diff_tool(
            tool_name="update_file",
            message="Changed",
            diff=diff,
            args={"path": "file.py", "mode": "replace"},
        )
        assert isinstance(result, Panel)

    def test_with_duration(self) -> None:
        diff = "-a\n+b"
        result = RichPanelRenderer.render_diff_tool(
            tool_name="edit",
            message="Edited",
            diff=diff,
            duration_ms=50.0,
        )
        assert isinstance(result, Panel)

    def test_with_timestamp(self) -> None:
        diff = "-x\n+y"
        result = RichPanelRenderer.render_diff_tool(
            tool_name="edit",
            message="Edited",
            diff=diff,
            timestamp=datetime(2025, 6, 1, 12, 0, 0),
        )
        assert isinstance(result, Panel)
        assert result.subtitle is not None

    def test_empty_message(self) -> None:
        diff = "-old\n+new"
        result = RichPanelRenderer.render_diff_tool(
            tool_name="update_file",
            message="",
            diff=diff,
        )
        assert isinstance(result, Panel)

    def test_no_args_no_duration_no_timestamp(self) -> None:
        diff = "+added line"
        result = RichPanelRenderer.render_diff_tool(
            tool_name="write",
            message="Created file",
            diff=diff,
        )
        assert isinstance(result, Panel)


class TestRichPanelRendererError:
    """RichPanelRenderer.render_error builds error panels."""

    def test_error_severity(self) -> None:
        data = ErrorDisplayData(
            error_type="RuntimeError",
            message="something failed",
            severity="error",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_warning_severity(self) -> None:
        data = ErrorDisplayData(
            error_type="ConfigWarning",
            message="deprecated option",
            severity="warning",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_info_severity(self) -> None:
        data = ErrorDisplayData(
            error_type="Notice",
            message="operation cancelled",
            severity="info",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_unknown_severity_defaults_to_error(self) -> None:
        data = ErrorDisplayData(
            error_type="WeirdError",
            message="something odd",
            severity="critical",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_with_suggested_fix(self) -> None:
        data = ErrorDisplayData(
            error_type="FileError",
            message="not found",
            suggested_fix="Check the path",
            severity="error",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_with_recovery_commands(self) -> None:
        data = ErrorDisplayData(
            error_type="GitError",
            message="merge conflict",
            recovery_commands=["git status", "git stash"],
            severity="error",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_with_context(self) -> None:
        data = ErrorDisplayData(
            error_type="ToolError",
            message="execution failed",
            context={"Tool": "bash", "Path": "/tmp"},
            severity="error",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)

    def test_with_all_fields(self) -> None:
        data = ErrorDisplayData(
            error_type="CompleteError",
            message="total failure",
            suggested_fix="Try again",
            recovery_commands=["cmd1", "cmd2"],
            context={"Key": "Value"},
            severity="error",
        )
        result = RichPanelRenderer.render_error(data)
        assert isinstance(result, Panel)


class TestRichPanelRendererSearchResults:
    """RichPanelRenderer.render_search_results builds search panels."""

    def test_basic_search_results(self) -> None:
        data = SearchResultData(
            query="test",
            results=[{"title": "file.py", "snippet": "test line"}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_with_search_time(self) -> None:
        data = SearchResultData(
            query="func",
            results=[{"title": "a.py", "snippet": "def func():"}],
            total_count=1,
            search_time_ms=33.7,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_multiple_pages(self) -> None:
        results = [{"title": f"f{i}.py", "snippet": f"line {i}"} for i in range(30)]
        data = SearchResultData(
            query="multi",
            results=results,
            total_count=30,
            current_page=2,
            page_size=10,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_result_with_relevance(self) -> None:
        data = SearchResultData(
            query="scored",
            results=[{"title": "a.py", "snippet": "hit", "relevance": 0.92}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_result_without_snippet(self) -> None:
        data = SearchResultData(
            query="bare",
            results=[{"title": "bare.py"}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_result_with_content_key(self) -> None:
        data = SearchResultData(
            query="content",
            results=[{"title": "c.py", "content": "some content here"}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_result_with_score_key(self) -> None:
        data = SearchResultData(
            query="alt_score",
            results=[{"title": "s.py", "snippet": "x", "score": 0.75}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_result_with_name_key_fallback(self) -> None:
        data = SearchResultData(
            query="named",
            results=[{"name": "something", "snippet": "context"}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_result_with_no_identifying_keys(self) -> None:
        data = SearchResultData(
            query="anon",
            results=[{"snippet": "only snippet"}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)

    def test_source_index_subtitle(self) -> None:
        data = SearchResultData(
            query="q",
            results=[{"title": "f.py", "snippet": "x"}],
            total_count=1,
            source="index",
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)
        assert result.subtitle is not None
        assert "Indexed" in str(result.subtitle)

    def test_source_filesystem_subtitle(self) -> None:
        data = SearchResultData(
            query="q",
            results=[{"title": "f.py", "snippet": "x"}],
            total_count=1,
            source="filesystem",
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)
        assert result.subtitle is not None
        assert "Scanned" in str(result.subtitle)

    def test_no_source_single_page_no_subtitle(self) -> None:
        data = SearchResultData(
            query="q",
            results=[{"title": "f.py", "snippet": "x"}],
            total_count=1,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)
        # Single page, no source => no subtitle
        assert result.subtitle is None

    def test_many_results_truncated_with_more_indicator(self) -> None:
        """When results exceed MAX_SEARCH_RESULTS_DISPLAY, the panel shows +N more."""
        results = [{"title": f"f{i}.py", "snippet": f"line {i}"} for i in range(50)]
        data = SearchResultData(
            query="big",
            results=results,
            total_count=50,
            page_size=50,
        )
        result = RichPanelRenderer.render_search_results(data)
        assert isinstance(result, Panel)


class TestRichPanelRendererInfoSuccessWarning:
    """RichPanelRenderer.render_info/render_success/render_warning."""

    def test_info_with_string_content(self) -> None:
        result = RichPanelRenderer.render_info("Title", "Some information")
        assert isinstance(result, Panel)

    def test_info_with_rich_renderable_content(self) -> None:
        content = Text("styled info", style="bold")
        result = RichPanelRenderer.render_info("Title", content)
        assert isinstance(result, Panel)

    def test_success_panel(self) -> None:
        result = RichPanelRenderer.render_success("Done", "Operation completed")
        assert isinstance(result, Panel)

    def test_warning_panel(self) -> None:
        result = RichPanelRenderer.render_warning("Caution", "Proceed carefully")
        assert isinstance(result, Panel)


# ===================================================================
# panels.py — module-level convenience functions
# ===================================================================


class TestToolPanelConvenience:
    """tool_panel convenience function."""

    def test_basic_tool_panel(self) -> None:
        result = tool_panel(
            "bash",
            "completed",
            args={"command": "echo test"},
            result="test",
            duration_ms=10.0,
            max_line_width=80,
        )
        assert isinstance(result, Panel)

    def test_no_args_no_result(self) -> None:
        result = tool_panel(
            "noop",
            "running",
            duration_ms=None,
            max_line_width=80,
        )
        assert isinstance(result, Panel)


class TestErrorPanelConvenience:
    """error_panel convenience function."""

    def test_basic_error_panel(self) -> None:
        result = error_panel("FileError", "File not found")
        assert isinstance(result, Panel)

    def test_with_fix_and_recovery(self) -> None:
        result = error_panel(
            "GitError",
            "Merge conflict",
            suggested_fix="Resolve conflicts",
            recovery_commands=["git status", "git merge --abort"],
            severity="error",
        )
        assert isinstance(result, Panel)

    def test_warning_severity(self) -> None:
        result = error_panel(
            "ConfigWarning",
            "Deprecated option",
            severity="warning",
        )
        assert isinstance(result, Panel)


class TestSearchPanelConvenience:
    """search_panel convenience function."""

    def test_basic_search_panel(self) -> None:
        results = [{"title": "a.py", "snippet": "match"}]
        result = search_panel("query", results)
        assert isinstance(result, Panel)

    def test_with_total_count_override(self) -> None:
        results = [{"title": "a.py", "snippet": "match"}]
        result = search_panel("query", results, total_count=100)
        assert isinstance(result, Panel)

    def test_with_page_and_search_time(self) -> None:
        results = [{"title": "a.py", "snippet": "match"}]
        result = search_panel("query", results, page=2, search_time_ms=20.0)
        assert isinstance(result, Panel)


class TestToolPanelSmart:
    """tool_panel_smart routes to specialized renderers."""

    def test_non_completed_falls_back_to_generic(self) -> None:
        result = tool_panel_smart(
            "bash",
            "running",
            args={"command": "ls"},
            duration_ms=None,
            max_line_width=80,
        )
        assert isinstance(result, Panel)

    def test_completed_without_result_falls_back(self) -> None:
        result = tool_panel_smart(
            "bash",
            "completed",
            args={"command": "echo"},
            result=None,
            duration_ms=5.0,
            max_line_width=80,
        )
        assert isinstance(result, Panel)

    def test_completed_unknown_tool_falls_back(self) -> None:
        result = tool_panel_smart(
            "custom_tool",
            "completed",
            args={},
            result="some output",
            duration_ms=10.0,
            max_line_width=80,
        )
        assert isinstance(result, Panel)

    def test_failed_status_falls_back(self) -> None:
        result = tool_panel_smart(
            "bash",
            "failed",
            args={"command": "bad"},
            result="error output",
            duration_ms=1.0,
            max_line_width=80,
        )
        assert isinstance(result, Panel)


# ===================================================================
# errors.py — render functions for deep coverage
# ===================================================================


class TestRenderToolErrorDeep:
    """Deeper paths in render_tool_error."""

    def test_with_file_path_includes_recovery_commands(self) -> None:
        result = render_tool_error(
            "read_file",
            "not found",
            file_path="/tmp/missing.py",
        )
        assert isinstance(result, Panel)

    def test_without_file_path_generic_recovery(self) -> None:
        result = render_tool_error("grep", "bad pattern")
        assert isinstance(result, Panel)

    def test_with_all_params(self) -> None:
        result = render_tool_error(
            "write_file",
            "permission denied",
            suggested_fix="Check directory permissions",
            file_path="/etc/hosts",
        )
        assert isinstance(result, Panel)

    def test_empty_message(self) -> None:
        result = render_tool_error("bash", "")
        assert isinstance(result, Panel)


class TestRenderValidationErrorDeep:
    """Deeper paths in render_validation_error."""

    def test_without_examples(self) -> None:
        result = render_validation_error("timeout", "must be positive integer")
        assert isinstance(result, Panel)

    def test_with_examples(self) -> None:
        result = render_validation_error(
            "model",
            "not recognized",
            valid_examples=["gpt-4", "claude-3"],
        )
        assert isinstance(result, Panel)

    def test_with_many_examples_truncates(self) -> None:
        result = render_validation_error(
            "color",
            "invalid",
            valid_examples=["red", "green", "blue", "yellow", "purple"],
        )
        assert isinstance(result, Panel)

    def test_empty_examples_list(self) -> None:
        result = render_validation_error(
            "field",
            "bad value",
            valid_examples=[],
        )
        assert isinstance(result, Panel)


class TestRenderUserAbortDeep:
    """render_user_abort returns info-severity panel."""

    def test_returns_panel(self) -> None:
        result = render_user_abort()
        assert isinstance(result, Panel)

    def test_title_contains_cancelled(self) -> None:
        result = render_user_abort()
        assert isinstance(result, Panel)
        assert "Cancelled" in str(result.title)


class TestRenderCatastrophicErrorDeep:
    """render_catastrophic_error covers unexpected failures."""

    def test_basic_exception(self) -> None:
        result = render_catastrophic_error(RuntimeError("boom"))
        assert isinstance(result, Panel)

    def test_empty_exception_message(self) -> None:
        result = render_catastrophic_error(RuntimeError(""))
        assert isinstance(result, Panel)

    def test_very_long_exception_truncated(self) -> None:
        result = render_catastrophic_error(RuntimeError("x" * 500))
        assert isinstance(result, Panel)

    def test_with_context_param(self) -> None:
        result = render_catastrophic_error(
            ValueError("bad"), context="during processing"
        )
        assert isinstance(result, Panel)

    def test_exception_type_name_used_when_empty(self) -> None:
        """When str(exc) is empty, type(exc).__name__ is used as fallback."""
        result = render_catastrophic_error(RuntimeError(""))
        assert isinstance(result, Panel)
        assert "Something Went Wrong" in str(result.title)


class TestRenderConnectionError:
    """render_connection_error builds connection error panels."""

    def test_with_retry_available(self) -> None:
        result = render_connection_error(
            "OpenAI", "Connection timed out", retry_available=True
        )
        assert isinstance(result, Panel)

    def test_without_retry(self) -> None:
        result = render_connection_error(
            "Anthropic", "Service unavailable", retry_available=False
        )
        assert isinstance(result, Panel)

    def test_title_contains_service_name(self) -> None:
        result = render_connection_error("GitHub", "Rate limited")
        assert isinstance(result, Panel)
        assert "GitHub" in str(result.title)


class TestRenderException:
    """render_exception handles arbitrary exceptions."""

    def test_plain_exception(self) -> None:
        result = render_exception(Exception("generic error"))
        assert isinstance(result, Panel)

    def test_runtime_error(self) -> None:
        result = render_exception(RuntimeError("runtime issue"))
        assert isinstance(result, Panel)

    def test_value_error(self) -> None:
        result = render_exception(ValueError("bad input"))
        assert isinstance(result, Panel)

    def test_exception_with_tool_name_attr(self) -> None:
        exc = Exception("tool failed")
        exc.tool_name = "bash"  # type: ignore[attr-defined]
        result = render_exception(exc)
        assert isinstance(result, Panel)

    def test_exception_with_suggested_fix_attr(self) -> None:
        exc = Exception("config error")
        exc.suggested_fix = "Reconfigure the settings"  # type: ignore[attr-defined]
        result = render_exception(exc)
        assert isinstance(result, Panel)

    def test_exception_with_recovery_commands_attr(self) -> None:
        exc = Exception("recoverable error")
        exc.recovery_commands = ["cmd1", "cmd2"]  # type: ignore[attr-defined]
        result = render_exception(exc)
        assert isinstance(result, Panel)

    def test_exception_message_with_fix_prefix_stripped(self) -> None:
        exc = Exception("Something failed Fix: do this instead")
        result = render_exception(exc)
        assert isinstance(result, Panel)

    def test_exception_message_with_suggested_fix_prefix(self) -> None:
        exc = Exception("Error occurred Suggested fix: try this")
        result = render_exception(exc)
        assert isinstance(result, Panel)
