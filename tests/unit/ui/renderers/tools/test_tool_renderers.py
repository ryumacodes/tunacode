"""Tests for render methods (build_header, build_params, build_viewport, build_status, render)
across all tool renderers.

Existing test_tool_parse_result.py covers parse_result(); this file
exercises the Rich-object-producing methods that were previously uncovered.

Source: src/tunacode/ui/renderers/tools/*.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from tunacode.ui.renderers.tools.base import RendererConfig
from tunacode.ui.renderers.tools.bash import BashData, BashRenderer
from tunacode.ui.renderers.tools.glob import GlobData, GlobRenderer
from tunacode.ui.renderers.tools.grep import GrepData, GrepRenderer
from tunacode.ui.renderers.tools.list_dir import ListDirData, ListDirRenderer
from tunacode.ui.renderers.tools.read_file import ReadFileData, ReadFileRenderer
from tunacode.ui.renderers.tools.update_file import UpdateFileData, UpdateFileRenderer
from tunacode.ui.renderers.tools.web_fetch import WebFetchData, WebFetchRenderer
from tunacode.ui.renderers.tools.write_file import WriteFileData, WriteFileRenderer

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

DEFAULT_MAX_WIDTH = 80
DEFAULT_DURATION = 123.4


def _cfg(tool_name: str) -> RendererConfig:
    return RendererConfig(tool_name=tool_name)


# ---------------------------------------------------------------------------
# BashRenderer zone methods
# ---------------------------------------------------------------------------


class TestBashRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = BashRenderer(_cfg("bash"))
        self.data_ok = BashData(
            command="ls -la",
            exit_code=0,
            working_dir="/home/user",
            stdout="file1.txt\nfile2.txt",
            stderr="",
            is_truncated=False,
            timeout=30,
        )
        self.data_err = BashData(
            command="false",
            exit_code=1,
            working_dir="/tmp",
            stdout="",
            stderr="command failed",
            is_truncated=True,
            timeout=60,
        )

    # -- build_header --

    def test_header_success(self) -> None:
        header = self.renderer.build_header(
            self.data_ok, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert "ls -la" in header.plain
        assert "ok" in header.plain

    def test_header_failure(self) -> None:
        header = self.renderer.build_header(
            self.data_err, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert "exit 1" in header.plain

    def test_header_long_command_truncated(self) -> None:
        long_cmd = BashData(
            command="a" * 200,
            exit_code=0,
            working_dir=".",
            stdout="",
            stderr="",
            is_truncated=False,
            timeout=30,
        )
        header = self.renderer.build_header(long_cmd, None, 50)
        assert isinstance(header, Text)
        assert "..." in header.plain

    # -- build_params --

    def test_params_contains_cwd_and_timeout(self) -> None:
        params = self.renderer.build_params(self.data_ok, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        plain = params.plain
        assert "cwd:" in plain
        assert "/home/user" in plain
        assert "timeout:" in plain
        assert "30s" in plain

    # -- build_viewport --

    def test_viewport_with_stdout(self) -> None:
        result = self.renderer.build_viewport(self.data_ok, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_viewport_with_stderr(self) -> None:
        result = self.renderer.build_viewport(self.data_err, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_viewport_no_output(self) -> None:
        empty = BashData(
            command="true",
            exit_code=0,
            working_dir=".",
            stdout="",
            stderr="",
            is_truncated=False,
            timeout=30,
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_viewport_with_both_streams(self) -> None:
        both = BashData(
            command="make",
            exit_code=2,
            working_dir="/project",
            stdout="Building...\nDone",
            stderr="warning: unused variable",
            is_truncated=False,
            timeout=120,
        )
        result = self.renderer.build_viewport(both, DEFAULT_MAX_WIDTH)
        assert result is not None

    # -- build_status --

    def test_status_with_duration(self) -> None:
        status = self.renderer.build_status(
            self.data_ok, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "123ms" in status.plain

    def test_status_truncated(self) -> None:
        status = self.renderer.build_status(
            self.data_err, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert "(truncated)" in status.plain

    def test_status_no_duration(self) -> None:
        status = self.renderer.build_status(
            self.data_ok, None, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "ms" not in status.plain

    def test_status_empty_output(self) -> None:
        empty = BashData(
            command="true",
            exit_code=0,
            working_dir=".",
            stdout="",
            stderr="",
            is_truncated=False,
            timeout=30,
        )
        status = self.renderer.build_status(empty, None, DEFAULT_MAX_WIDTH)
        assert isinstance(status, Text)

    # -- border / status text --

    def test_border_color_success(self) -> None:
        color = self.renderer.get_border_color(self.data_ok)
        assert color == self.renderer.config.success_color

    def test_border_color_failure(self) -> None:
        color = self.renderer.get_border_color(self.data_err)
        assert color == self.renderer.config.warning_color

    def test_status_text_success(self) -> None:
        assert self.renderer.get_status_text(self.data_ok) == "done"

    def test_status_text_failure(self) -> None:
        assert self.renderer.get_status_text(self.data_err) == "exit 1"

    # -- full render --

    def test_render_success(self) -> None:
        raw = (
            "Command: ls\n"
            "Exit Code: 0\n"
            "Working Directory: /home\n\n"
            "STDOUT:\nfile.txt\n\n"
            "STDERR:\n(no errors)"
        )
        panel = self.renderer.render(None, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH)
        assert isinstance(panel, Panel)

    def test_render_failure_exit_code(self) -> None:
        raw = (
            "Command: bad_cmd\n"
            "Exit Code: 127\n"
            "Working Directory: /tmp\n\n"
            "STDOUT:\n(no output)\n\n"
            "STDERR:\ncommand not found"
        )
        panel = self.renderer.render(None, raw, 50.0, DEFAULT_MAX_WIDTH)
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(None, "", None, DEFAULT_MAX_WIDTH) is None

    def test_render_returns_none_for_garbage(self) -> None:
        assert self.renderer.render(None, "garbage", None, DEFAULT_MAX_WIDTH) is None


# ---------------------------------------------------------------------------
# GrepRenderer zone methods
# ---------------------------------------------------------------------------


class TestGrepRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = GrepRenderer(_cfg("grep"))
        self.data = GrepData(
            pattern="TODO",
            total_matches=3,
            strategy="smart",
            candidates=42,
            matches=[
                {
                    "file": "src/main.py", "line": 10,
                    "before": "# ", "match": "TODO", "after": ": fix",
                },
                {
                    "file": "src/main.py", "line": 25,
                    "before": "# ", "match": "TODO", "after": ": refactor",
                },
                {
                    "file": "src/utils.py", "line": 5,
                    "before": "# ", "match": "TODO", "after": "",
                },
            ],
            is_truncated=False,
            case_sensitive=True,
            use_regex=False,
            context_lines=2,
        )

    def test_header_pattern_and_count(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert '"TODO"' in header.plain
        assert "3 matches" in header.plain

    def test_header_singular_match(self) -> None:
        single = GrepData(
            pattern="FIXME",
            total_matches=1,
            strategy="smart",
            candidates=10,
            matches=[{
                "file": "a.py", "line": 1,
                "before": "", "match": "FIXME", "after": "",
            }],
            is_truncated=False,
            case_sensitive=False,
            use_regex=False,
            context_lines=0,
        )
        header = self.renderer.build_header(single, None, DEFAULT_MAX_WIDTH)
        assert "1 match" in header.plain
        assert "1 matches" not in header.plain

    def test_params_contains_flags(self) -> None:
        params = self.renderer.build_params(self.data, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        plain = params.plain
        assert "strategy:" in plain
        assert "smart" in plain
        assert "case:" in plain
        assert "yes" in plain
        assert "regex:" in plain
        assert "no" in plain
        assert "context:" in plain

    def test_params_case_insensitive_regex_on(self) -> None:
        data = GrepData(
            pattern="x", total_matches=0, strategy="regex",
            candidates=0, matches=[], is_truncated=False,
            case_sensitive=False, use_regex=True, context_lines=5,
        )
        params = self.renderer.build_params(data, DEFAULT_MAX_WIDTH)
        plain = params.plain
        # case: no, regex: yes
        assert "no" in plain
        assert "yes" in plain

    def test_viewport_with_matches(self) -> None:
        result = self.renderer.build_viewport(self.data, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_viewport_no_matches(self) -> None:
        empty = GrepData(
            pattern="nonexistent", total_matches=0, strategy="smart",
            candidates=0, matches=[], is_truncated=False,
            case_sensitive=False, use_regex=False, context_lines=2,
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)
        assert "no matches" in result.plain

    def test_status_with_candidates_and_duration(self) -> None:
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "42 files searched" in status.plain
        assert "123ms" in status.plain

    def test_status_truncated(self) -> None:
        data = GrepData(
            pattern="x", total_matches=100, strategy="smart",
            candidates=50,
            matches=[{
                "file": "a.py", "line": 1,
                "before": "", "match": "x", "after": "",
            }],
            is_truncated=True,
            case_sensitive=False, use_regex=False, context_lines=2,
        )
        status = self.renderer.build_status(data, None, DEFAULT_MAX_WIDTH)
        assert "[1/100 shown]" in status.plain

    def test_status_no_items(self) -> None:
        data = GrepData(
            pattern="x", total_matches=1, strategy="smart",
            candidates=0,
            matches=[{
                "file": "a.py", "line": 1,
                "before": "", "match": "x", "after": "",
            }],
            is_truncated=False,
            case_sensitive=False, use_regex=False, context_lines=2,
        )
        status = self.renderer.build_status(data, None, DEFAULT_MAX_WIDTH)
        assert isinstance(status, Text)

    # -- full render --

    def test_render_valid_result(self) -> None:
        raw = (
            "Found 1 match for pattern: TODO\n"
            "Strategy: smart | Candidates: 5 files\n"
            "\U0001f4c1 src/main.py:10\n"
            "\u25b6  10\u2502# \u27e8TODO\u27e9: fix this"
        )
        panel = self.renderer.render(
            None, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(None, "", None, DEFAULT_MAX_WIDTH) is None


# ---------------------------------------------------------------------------
# GlobRenderer zone methods
# ---------------------------------------------------------------------------


class TestGlobRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = GlobRenderer(_cfg("glob"))
        self.data = GlobData(
            pattern="**/*.py",
            file_count=5,
            files=[
                "src/main.py",
                "src/utils.py",
                "tests/test_main.py",
                "setup.py",
                "docs/conf.py",
            ],
            source="index",
            is_truncated=False,
            recursive=True,
            include_hidden=False,
            sort_by="modified",
        )

    def test_header_pattern_and_count(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert '"**/*.py"' in header.plain
        assert "5 files" in header.plain

    def test_header_single_file(self) -> None:
        single = GlobData(
            pattern="*.txt", file_count=1, files=["readme.txt"],
            source="filesystem", is_truncated=False,
            recursive=False, include_hidden=False, sort_by="name",
        )
        header = self.renderer.build_header(
            single, None, DEFAULT_MAX_WIDTH,
        )
        assert "1 file" in header.plain
        assert "1 files" not in header.plain

    def test_params_contains_flags(self) -> None:
        params = self.renderer.build_params(self.data, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        plain = params.plain
        assert "recursive:" in plain
        assert "on" in plain
        assert "hidden:" in plain
        assert "off" in plain
        assert "sort:" in plain
        assert "modified" in plain

    def test_params_hidden_on(self) -> None:
        data = GlobData(
            pattern="*", file_count=0, files=[],
            source="filesystem", is_truncated=False,
            recursive=False, include_hidden=True, sort_by="name",
        )
        params = self.renderer.build_params(data, DEFAULT_MAX_WIDTH)
        plain = params.plain
        assert "off" in plain  # recursive
        assert "on" in plain   # hidden

    def test_viewport_with_files(self) -> None:
        result = self.renderer.build_viewport(self.data, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_viewport_no_files(self) -> None:
        empty = GlobData(
            pattern="*.xyz", file_count=0, files=[],
            source="filesystem", is_truncated=False,
            recursive=True, include_hidden=False, sort_by="name",
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)
        assert "no files" in result.plain

    def test_viewport_varied_file_types(self) -> None:
        data = GlobData(
            pattern="*", file_count=3,
            files=["src/main.py", "README.md", "data.json"],
            source="filesystem", is_truncated=False,
            recursive=True, include_hidden=False, sort_by="name",
        )
        result = self.renderer.build_viewport(data, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_status_indexed(self) -> None:
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "indexed" in status.plain
        assert "123ms" in status.plain

    def test_status_scanned(self) -> None:
        data = GlobData(
            pattern="*", file_count=2, files=["a.txt", "b.txt"],
            source="filesystem", is_truncated=False,
            recursive=True, include_hidden=False, sort_by="name",
        )
        status = self.renderer.build_status(data, None, DEFAULT_MAX_WIDTH)
        assert "scanned" in status.plain

    def test_status_truncated(self) -> None:
        data = GlobData(
            pattern="*", file_count=100, files=["a.txt"],
            source="index", is_truncated=True,
            recursive=True, include_hidden=False, sort_by="name",
        )
        status = self.renderer.build_status(data, None, DEFAULT_MAX_WIDTH)
        assert "shown" in status.plain

    # -- full render --

    def test_render_valid_result(self) -> None:
        raw = (
            "[source:index]\n"
            "Found 2 files matching pattern: *.py\n\n"
            "src/main.py\n"
            "src/utils.py"
        )
        panel = self.renderer.render(
            None, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(None, "", None, DEFAULT_MAX_WIDTH) is None


# ---------------------------------------------------------------------------
# ListDirRenderer zone methods
# ---------------------------------------------------------------------------


class TestListDirRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = ListDirRenderer(_cfg("list_dir"))
        tree = (
            "src\n"
            "\u251c\u2500\u2500 main.py\n"
            "\u251c\u2500\u2500 utils.py\n"
            "\u2514\u2500\u2500 tests/"
        )
        self.data = ListDirData(
            directory="src",
            tree_content=tree,
            file_count=10,
            dir_count=3,
            is_truncated=False,
            max_files=100,
            show_hidden=False,
            ignore_count=5,
        )

    def test_header_dir_and_counts(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        plain = header.plain
        assert "src" in plain
        assert "10 files" in plain
        assert "3 dirs" in plain

    def test_params_contains_flags(self) -> None:
        params = self.renderer.build_params(self.data, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        plain = params.plain
        assert "hidden:" in plain
        assert "off" in plain
        assert "max:" in plain
        assert "100" in plain
        assert "ignore:" in plain
        assert "5" in plain

    def test_params_show_hidden_on(self) -> None:
        data = ListDirData(
            directory="/tmp",
            tree_content="/tmp\n\u2514\u2500\u2500 .hidden",
            file_count=1, dir_count=0, is_truncated=False,
            max_files=50, show_hidden=True, ignore_count=0,
        )
        params = self.renderer.build_params(data, DEFAULT_MAX_WIDTH)
        assert "on" in params.plain

    def test_viewport_with_tree_content(self) -> None:
        result = self.renderer.build_viewport(self.data, DEFAULT_MAX_WIDTH)
        assert result is not None

    def test_viewport_empty_directory(self) -> None:
        empty = ListDirData(
            directory="empty_dir",
            tree_content="empty_dir",
            file_count=0, dir_count=0, is_truncated=False,
            max_files=100, show_hidden=False, ignore_count=0,
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)
        assert "empty directory" in result.plain

    def test_style_tree_line_directory(self) -> None:
        styled = self.renderer._style_tree_line(
            "\u251c\u2500\u2500 tests/",
        )
        assert isinstance(styled, Text)

    def test_style_tree_line_file(self) -> None:
        styled = self.renderer._style_tree_line(
            "\u2514\u2500\u2500 main.py",
        )
        assert isinstance(styled, Text)

    def test_status_with_duration(self) -> None:
        self.renderer.build_viewport(self.data, DEFAULT_MAX_WIDTH)
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "123ms" in status.plain

    def test_status_truncated(self) -> None:
        lines = "\n".join(
            f"\u251c\u2500\u2500 file{i}.py" for i in range(20)
        )
        data = ListDirData(
            directory="/big",
            tree_content="/big\n" + lines,
            file_count=500, dir_count=10, is_truncated=True,
            max_files=100, show_hidden=False, ignore_count=50,
        )
        self.renderer.build_viewport(data, DEFAULT_MAX_WIDTH)
        status = self.renderer.build_status(data, None, DEFAULT_MAX_WIDTH)
        assert "(truncated)" in status.plain

    def test_status_no_data(self) -> None:
        data = ListDirData(
            directory="x",
            tree_content="x\n\u2514\u2500\u2500 a.txt",
            file_count=1, dir_count=0, is_truncated=False,
            max_files=100, show_hidden=False, ignore_count=0,
            shown_lines=1, total_lines=1,
        )
        status = self.renderer.build_status(data, None, DEFAULT_MAX_WIDTH)
        assert isinstance(status, Text)

    # -- full render --

    def test_render_valid_result(self) -> None:
        raw = (
            "10 files  3 dirs  5 ignored\n"
            "src\n"
            "\u251c\u2500\u2500 main.py\n"
            "\u2514\u2500\u2500 utils.py"
        )
        panel = self.renderer.render(
            None, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(None, "", None, DEFAULT_MAX_WIDTH) is None


# ---------------------------------------------------------------------------
# ReadFileRenderer zone methods
# ---------------------------------------------------------------------------


class TestReadFileRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = ReadFileRenderer(_cfg("read_file"))
        self.data = ReadFileData(
            filepath="/project/src/main.py",
            filename="main.py",
            root_path=Path("/project"),
            content_lines=[
                (1, "import os"),
                (2, "import sys"),
                (3, ""),
                (4, 'print("hello")'),
            ],
            total_lines=50,
            offset=0,
            has_more=True,
            end_message="(File has more lines beyond line 4)",
        )

    def test_header_filename_and_range(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert "main.py" in header.plain
        assert "lines 1-4" in header.plain

    def test_header_no_content_lines(self) -> None:
        data = ReadFileData(
            filepath="empty.py", filename="empty.py",
            root_path=Path("/"),
            content_lines=[], total_lines=0, offset=0,
            has_more=False, end_message="",
        )
        header = self.renderer.build_header(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert "empty.py" in header.plain

    def test_params_contains_filepath(self) -> None:
        params = self.renderer.build_params(self.data, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        assert "src/main.py" in params.plain

    def test_viewport_with_content(self) -> None:
        result = self.renderer.build_viewport(
            self.data, DEFAULT_MAX_WIDTH,
        )
        assert result is not None

    def test_viewport_empty_file(self) -> None:
        empty = ReadFileData(
            filepath="empty.py", filename="empty.py",
            root_path=Path("/"),
            content_lines=[], total_lines=0, offset=0,
            has_more=False, end_message="",
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)
        assert "empty file" in result.plain

    def test_viewport_python_gets_syntax(self) -> None:
        result = self.renderer.build_viewport(
            self.data, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(result, Syntax)

    def test_viewport_text_file_plain(self) -> None:
        data = ReadFileData(
            filepath="notes.txt", filename="notes.txt",
            root_path=Path("/"),
            content_lines=[(1, "Some notes"), (2, "More notes")],
            total_lines=2, offset=0,
            has_more=False, end_message="",
        )
        result = self.renderer.build_viewport(data, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)

    def test_status_has_more(self) -> None:
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        plain = status.plain
        assert "total: 50 lines" in plain
        assert "(more available)" in plain
        assert "123ms" in plain

    def test_status_complete_file(self) -> None:
        data = ReadFileData(
            filepath="small.py", filename="small.py",
            root_path=Path("/"),
            content_lines=[(1, "pass")],
            total_lines=1, offset=0,
            has_more=False,
            end_message="(End of file - total 1 lines)",
        )
        status = self.renderer.build_status(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "total: 1 lines" in status.plain
        assert "(more available)" not in status.plain

    def test_status_empty(self) -> None:
        data = ReadFileData(
            filepath="x.py", filename="x.py",
            root_path=Path("/"),
            content_lines=[], total_lines=0, offset=0,
            has_more=False, end_message="",
        )
        status = self.renderer.build_status(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)

    # -- full render --

    def test_render_valid_result(self) -> None:
        raw = (
            "<file>\n"
            "00001| import os\n"
            "00002| import sys\n"
            "(End of file - total 2 lines)\n"
            "</file>"
        )
        args: dict[str, Any] = {"filepath": "src/main.py"}
        panel = self.renderer.render(
            args, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(None, "", None, DEFAULT_MAX_WIDTH) is None


# ---------------------------------------------------------------------------
# WriteFileRenderer zone methods
# ---------------------------------------------------------------------------


class TestWriteFileRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = WriteFileRenderer(_cfg("write_file"))
        self.data = WriteFileData(
            filepath="/project/src/new_file.py",
            filename="new_file.py",
            root_path=Path("/project"),
            content='print("hello world")\n',
            line_count=1,
            is_success=True,
        )

    def test_header_filename_and_new(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        plain = header.plain
        assert "new_file.py" in plain
        assert "NEW" in plain
        assert "1 lines" in plain

    def test_params_contains_filepath(self) -> None:
        params = self.renderer.build_params(self.data, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        assert "src/new_file.py" in params.plain

    def test_viewport_with_content(self) -> None:
        result = self.renderer.build_viewport(
            self.data, DEFAULT_MAX_WIDTH,
        )
        assert result is not None

    def test_viewport_empty_content(self) -> None:
        empty = WriteFileData(
            filepath="empty.py", filename="empty.py",
            root_path=Path("/"),
            content="", line_count=0, is_success=True,
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)
        assert "empty file" in result.plain

    def test_viewport_python_gets_syntax(self) -> None:
        data = WriteFileData(
            filepath="script.py", filename="script.py",
            root_path=Path("/"),
            content="def foo():\n    return 42\n",
            line_count=2, is_success=True,
        )
        result = self.renderer.build_viewport(data, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Syntax)

    def test_status_with_duration(self) -> None:
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "123ms" in status.plain

    def test_status_truncated_file(self) -> None:
        big = WriteFileData(
            filepath="big.py", filename="big.py",
            root_path=Path("/"),
            content="\n".join(f"line {i}" for i in range(100)),
            line_count=100, is_success=True,
        )
        status = self.renderer.build_status(
            big, None, DEFAULT_MAX_WIDTH,
        )
        assert "lines" in status.plain

    def test_border_color_always_success(self) -> None:
        color = self.renderer.get_border_color(self.data)
        assert color == self.renderer.config.success_color

    # -- full render --

    def test_render_valid_result(self) -> None:
        args: dict[str, Any] = {
            "filepath": "/tmp/new.py", "content": "x = 1\n",
        }
        raw = "Successfully wrote to new file: /tmp/new.py"
        panel = self.renderer.render(
            args, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(None, "", None, DEFAULT_MAX_WIDTH) is None


# ---------------------------------------------------------------------------
# WebFetchRenderer zone methods
# ---------------------------------------------------------------------------


class TestWebFetchRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = WebFetchRenderer(_cfg("web_fetch"))
        self.data = WebFetchData(
            url="https://example.com/api/data",
            domain="example.com",
            content="Hello World\nLine 2\nLine 3",
            content_lines=3,
            is_truncated=False,
            timeout=60,
        )

    def test_header_domain_and_line_count(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert "example.com" in header.plain
        assert "3 lines" in header.plain

    def test_header_no_domain(self) -> None:
        data = WebFetchData(
            url="", domain="", content="x",
            content_lines=1, is_truncated=False, timeout=30,
        )
        header = self.renderer.build_header(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        assert "web" in header.plain

    def test_params_url_and_timeout(self) -> None:
        params = self.renderer.build_params(self.data, DEFAULT_MAX_WIDTH)
        assert isinstance(params, Text)
        plain = params.plain
        assert "url:" in plain
        assert "example.com" in plain
        assert "timeout:" in plain
        assert "60s" in plain

    def test_params_long_url_truncated(self) -> None:
        long_url = "https://x.com/" + "a" * 80
        data = WebFetchData(
            url=long_url, domain="x.com",
            content="x", content_lines=1,
            is_truncated=False, timeout=30,
        )
        params = self.renderer.build_params(data, DEFAULT_MAX_WIDTH)
        assert "..." in params.plain

    def test_viewport_with_content(self) -> None:
        result = self.renderer.build_viewport(
            self.data, DEFAULT_MAX_WIDTH,
        )
        assert result is not None

    def test_viewport_no_content(self) -> None:
        empty = WebFetchData(
            url="https://example.com", domain="example.com",
            content="", content_lines=0,
            is_truncated=False, timeout=30,
        )
        result = self.renderer.build_viewport(empty, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)
        assert "no content" in result.plain

    def test_viewport_json_detection(self) -> None:
        data = WebFetchData(
            url="https://api.example.com/data.json",
            domain="api.example.com",
            content='{"key": "value"}',
            content_lines=1, is_truncated=False, timeout=30,
        )
        result = self.renderer.build_viewport(data, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Syntax)

    def test_viewport_plain_text(self) -> None:
        data = WebFetchData(
            url="https://example.com/page",
            domain="example.com",
            content="Just some text.\nMore text.",
            content_lines=2, is_truncated=False, timeout=30,
        )
        result = self.renderer.build_viewport(data, DEFAULT_MAX_WIDTH)
        assert isinstance(result, Text)

    def test_status_with_duration(self) -> None:
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "123ms" in status.plain

    def test_status_truncated(self) -> None:
        data = WebFetchData(
            url="https://example.com", domain="example.com",
            content="[Content truncated due to size]\ndata",
            content_lines=2, is_truncated=True, timeout=30,
        )
        status = self.renderer.build_status(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert "(content truncated)" in status.plain

    def test_status_empty(self) -> None:
        data = WebFetchData(
            url="https://example.com", domain="example.com",
            content="short", content_lines=1,
            is_truncated=False, timeout=30,
        )
        status = self.renderer.build_status(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)

    # -- full render --

    def test_render_valid_result(self) -> None:
        args: dict[str, Any] = {
            "url": "https://example.com", "timeout": 60,
        }
        panel = self.renderer.render(
            args, "Hello World", DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(
            None, "", None, DEFAULT_MAX_WIDTH,
        ) is None


# ---------------------------------------------------------------------------
# UpdateFileRenderer zone methods
# ---------------------------------------------------------------------------


class TestUpdateFileRendererZones:
    """Exercise build_header / build_params / build_viewport / build_status."""

    def setup_method(self) -> None:
        self.renderer = UpdateFileRenderer(_cfg("update_file"))
        self.data = UpdateFileData(
            filepath="src/main.py",
            filename="main.py",
            root_path=Path.cwd(),
            message="File 'src/main.py' updated successfully.",
            diff_content=(
                "--- a/src/main.py\n"
                "+++ b/src/main.py\n"
                "@@ -1,3 +1,5 @@\n"
                " import os\n"
                "+import sys\n"
                "+import json\n"
                " \n"
                "-print('old')\n"
                "+print('new')\n"
            ),
            additions=3,
            deletions=1,
            hunks=1,
        )

    def test_header_filename_and_stats(self) -> None:
        header = self.renderer.build_header(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(header, Text)
        plain = header.plain
        assert "main.py" in plain
        assert "+3" in plain
        assert "-1" in plain

    def test_params_contains_filepath(self) -> None:
        params = self.renderer.build_params(
            self.data, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(params, Text)
        assert "src/main.py" in params.plain

    def test_viewport_renders_diff(self) -> None:
        result = self.renderer.build_viewport(
            self.data, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(result, Syntax)

    def test_status_contains_hunks(self) -> None:
        status = self.renderer.build_status(
            self.data, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(status, Text)
        assert "1 hunk" in status.plain
        assert "123ms" in status.plain

    def test_status_plural_hunks(self) -> None:
        data = UpdateFileData(
            filepath="x.py", filename="x.py",
            root_path=Path.cwd(), message="ok",
            diff_content=(
                "--- a/x.py\n+++ b/x.py\n"
                "@@ -1 +1 @@\n-a\n+b\n"
                "@@ -10 +10 @@\n-c\n+d\n"
            ),
            additions=2, deletions=2, hunks=2,
        )
        status = self.renderer.build_status(
            data, None, DEFAULT_MAX_WIDTH,
        )
        assert "2 hunks" in status.plain

    # -- full render (overridden in UpdateFileRenderer) --

    def test_render_valid_result(self) -> None:
        raw = (
            "File 'src/main.py' updated successfully.\n\n"
            "--- a/src/main.py\n"
            "+++ b/src/main.py\n"
            "@@ -1,3 +1,4 @@\n"
            " import os\n"
            "+import sys\n"
            " \n"
            " print('hello')\n"
        )
        panel = self.renderer.render(
            None, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_with_diagnostics(self) -> None:
        raw = (
            "File 'src/main.py' updated successfully.\n\n"
            "--- a/src/main.py\n"
            "+++ b/src/main.py\n"
            "@@ -1,2 +1,3 @@\n"
            " import os\n"
            "+import sys\n"
            " print('hello')\n"
            "\n"
            "<file_diagnostics>\n"
            "Error (line 10): type mismatch\n"
            "Warning (line 15): unused import\n"
            "</file_diagnostics>"
        )
        panel = self.renderer.render(
            None, raw, DEFAULT_DURATION, DEFAULT_MAX_WIDTH,
        )
        assert isinstance(panel, Panel)

    def test_render_returns_none_for_empty(self) -> None:
        assert self.renderer.render(
            None, "", None, DEFAULT_MAX_WIDTH,
        ) is None

    def test_render_returns_none_for_no_diff(self) -> None:
        result = self.renderer.render(
            None, "Some message without diff",
            None, DEFAULT_MAX_WIDTH,
        )
        assert result is None


# ---------------------------------------------------------------------------
# BaseToolRenderer common methods
# ---------------------------------------------------------------------------


class TestBaseToolRendererCommon:
    """Test base class methods shared across all renderers."""

    def setup_method(self) -> None:
        self.renderer = BashRenderer(_cfg("bash"))

    def test_build_separator(self) -> None:
        sep = self.renderer.build_separator()
        assert isinstance(sep, Text)
        assert len(sep.plain) > 0

    def test_pad_viewport_lines_below_minimum(self) -> None:
        padded = self.renderer.pad_viewport_lines(["one"])
        assert len(padded) >= 3  # MIN_VIEWPORT_LINES

    def test_pad_viewport_lines_at_minimum(self) -> None:
        padded = self.renderer.pad_viewport_lines(["a", "b", "c"])
        assert len(padded) == 3

    def test_pad_viewport_lines_above_minimum(self) -> None:
        padded = self.renderer.pad_viewport_lines(["a", "b", "c", "d", "e"])
        assert len(padded) == 5

    def test_default_get_border_color(self) -> None:
        renderer = WriteFileRenderer(_cfg("write_file"))
        data = WriteFileData(
            filepath="x.py", filename="x.py",
            root_path=Path("/"),
            content="", line_count=0, is_success=True,
        )
        assert renderer.get_border_color(data) == renderer.config.success_color

    def test_default_get_status_text(self) -> None:
        renderer = WriteFileRenderer(_cfg("write_file"))
        data = WriteFileData(
            filepath="x.py", filename="x.py",
            root_path=Path("/"),
            content="", line_count=0, is_success=True,
        )
        assert renderer.get_status_text(data) == "done"


# ---------------------------------------------------------------------------
# Bash _detect_output_type coverage
# ---------------------------------------------------------------------------


class TestBashDetectOutputType:
    """Exercise the private _detect_output_type method."""

    def setup_method(self) -> None:
        self.renderer = BashRenderer(_cfg("bash"))

    def test_json_command(self) -> None:
        result = self.renderer._detect_output_type(
            "curl -s http://api.com", '{"key": "val"}',
        )
        assert result == "json"

    def test_git_diff_command(self) -> None:
        result = self.renderer._detect_output_type(
            "git diff HEAD", "--- a/file\n+++ b/file",
        )
        assert result == "diff"

    def test_git_log_command(self) -> None:
        result = self.renderer._detect_output_type(
            "git log", "commit abc123\nAuthor: test",
        )
        assert result is None

    def test_python_command(self) -> None:
        result = self.renderer._detect_output_type(
            "python script.py", "output text",
        )
        assert result is None

    def test_plain_command(self) -> None:
        result = self.renderer._detect_output_type("ls", "file1\nfile2")
        assert result is None

    def test_json_flag_non_json_output(self) -> None:
        result = self.renderer._detect_output_type("cmd --json", "not json")
        assert result != "json"


# ---------------------------------------------------------------------------
# WebFetch _detect_content_type coverage
# ---------------------------------------------------------------------------


class TestWebFetchDetectContentType:
    """Exercise the private _detect_content_type method."""

    def setup_method(self) -> None:
        self.renderer = WebFetchRenderer(_cfg("web_fetch"))

    def test_json_url(self) -> None:
        result = self.renderer._detect_content_type(
            "https://api.com/data.json", '{"k":"v"}',
        )
        assert result == "json"

    def test_xml_url(self) -> None:
        result = self.renderer._detect_content_type(
            "https://site.com/feed.xml", "<rss>data</rss>",
        )
        assert result == "xml"

    def test_yaml_url(self) -> None:
        result = self.renderer._detect_content_type(
            "https://site.com/config.yaml", "key: value",
        )
        assert result == "yaml"

    def test_yml_url(self) -> None:
        result = self.renderer._detect_content_type(
            "https://site.com/config.yml", "key: value",
        )
        assert result == "yaml"

    def test_raw_github_python(self) -> None:
        url = "https://raw.githubusercontent.com/u/r/main/s.py"
        result = self.renderer._detect_content_type(url, "import os")
        assert result == "python"

    def test_raw_github_js(self) -> None:
        url = "https://raw.githubusercontent.com/u/r/main/a.js"
        result = self.renderer._detect_content_type(url, "const x=1;")
        assert result == "javascript"

    def test_raw_github_ts(self) -> None:
        url = "https://raw.githubusercontent.com/u/r/main/a.ts"
        result = self.renderer._detect_content_type(url, "const x=1;")
        assert result == "typescript"

    def test_raw_github_rust(self) -> None:
        url = "https://raw.githubusercontent.com/u/r/main/lib.rs"
        result = self.renderer._detect_content_type(url, "fn main(){}")
        assert result == "rust"

    def test_raw_github_go(self) -> None:
        url = "https://raw.githubusercontent.com/u/r/main/main.go"
        result = self.renderer._detect_content_type(url, "package main")
        assert result == "go"

    def test_api_url_json(self) -> None:
        result = self.renderer._detect_content_type(
            "https://example.com/api/users", '[{"name":"alice"}]',
        )
        assert result == "json"

    def test_rss_url(self) -> None:
        result = self.renderer._detect_content_type(
            "https://blog.example.com/rss", "<feed>x</feed>",
        )
        assert result == "xml"

    def test_atom_url(self) -> None:
        result = self.renderer._detect_content_type(
            "https://blog.example.com/atom", "<feed>x</feed>",
        )
        assert result == "xml"

    def test_plain_content(self) -> None:
        result = self.renderer._detect_content_type(
            "https://example.com/page", "Just some text.",
        )
        assert result is None


# ---------------------------------------------------------------------------
# Glob _get_file_style coverage
# ---------------------------------------------------------------------------


class TestGlobGetFileStyle:
    """Exercise the private _get_file_style method."""

    def setup_method(self) -> None:
        self.renderer = GlobRenderer(_cfg("glob"))

    def test_python_file(self) -> None:
        assert self.renderer._get_file_style("src/main.py") == "bright_blue"

    def test_javascript_file(self) -> None:
        assert self.renderer._get_file_style("app.js") == "yellow"

    def test_json_file(self) -> None:
        assert self.renderer._get_file_style("config.json") == "green"

    def test_markdown_file(self) -> None:
        assert self.renderer._get_file_style("README.md") == "cyan"

    def test_unknown_file(self) -> None:
        assert self.renderer._get_file_style("data.xyz") == ""

    def test_bash_file(self) -> None:
        assert self.renderer._get_file_style("run.sh") == "magenta"


# ---------------------------------------------------------------------------
# ListDir _style_tree_line / _get_file_style coverage
# ---------------------------------------------------------------------------


class TestListDirStyleTreeLine:
    """Exercise the private _style_tree_line method."""

    def setup_method(self) -> None:
        self.renderer = ListDirRenderer(_cfg("list_dir"))

    def test_directory_line(self) -> None:
        styled = self.renderer._style_tree_line("\u251c\u2500\u2500 subdir/")
        assert isinstance(styled, Text)

    def test_file_with_extension(self) -> None:
        styled = self.renderer._style_tree_line("\u2514\u2500\u2500 script.py")
        assert isinstance(styled, Text)

    def test_file_no_extension_treated_as_dir(self) -> None:
        styled = self.renderer._style_tree_line("\u2514\u2500\u2500 Makefile")
        assert isinstance(styled, Text)

    def test_deeply_nested_prefix(self) -> None:
        line = "\u2502   \u2502   \u2514\u2500\u2500 deep.rs"
        styled = self.renderer._style_tree_line(line)
        assert isinstance(styled, Text)

    def test_plain_name_no_prefix(self) -> None:
        styled = self.renderer._style_tree_line("toplevel.py")
        assert isinstance(styled, Text)


class TestListDirGetFileStyle:
    """Exercise the private _get_file_style method."""

    def setup_method(self) -> None:
        self.renderer = ListDirRenderer(_cfg("list_dir"))

    def test_python_file_color(self) -> None:
        assert self.renderer._get_file_style("main.py") == "bright_blue"

    def test_unknown_file_empty(self) -> None:
        assert self.renderer._get_file_style("data.xyz") == ""


# ---------------------------------------------------------------------------
# RendererConfig defaults
# ---------------------------------------------------------------------------


class TestRendererConfig:
    """Verify RendererConfig default values."""

    def test_defaults(self) -> None:
        config = RendererConfig(tool_name="test")
        assert config.tool_name == "test"
        assert config.success_color is not None
        assert config.warning_color is not None
        assert config.muted_color is not None

    def test_custom_colors(self) -> None:
        config = RendererConfig(
            tool_name="custom",
            success_color="green",
            warning_color="yellow",
            muted_color="gray",
        )
        assert config.success_color == "green"
        assert config.warning_color == "yellow"
        assert config.muted_color == "gray"
