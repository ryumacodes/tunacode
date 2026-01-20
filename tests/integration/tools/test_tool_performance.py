"""Tests for read_file, ripgrep execution, and grep integration."""

from __future__ import annotations

import builtins
from collections.abc import Callable, Iterable
from pathlib import Path

import pytest

import tunacode.tools.read_file as read_file_module
import tunacode.tools.utils.ripgrep as ripgrep_module
from tunacode.tools.grep import grep
from tunacode.tools.read_file import (
    LINE_NUMBER_PAD_WIDTH,
    LINE_NUMBER_SEPARATOR,
    MORE_LINES_MESSAGE,
)
from tunacode.tools.utils.ripgrep import RIPGREP_MATCH_FOUND_EXIT_CODE, RipgrepExecutor

EMPTY_TEXT = ""
NEWLINE = "\n"

READ_FILE_FILENAME = "sample.txt"
READ_FILE_ENCODING = "utf-8"
READ_FILE_LINE_ALPHA = f"alpha{NEWLINE}"
READ_FILE_LINE_BRAVO = f"bravo{NEWLINE}"
READ_FILE_LINE_CHARLIE = f"charlie{NEWLINE}"
READ_FILE_LINE_DELTA = f"delta{NEWLINE}"
READ_FILE_LINE_ECHO = f"echo{NEWLINE}"
READ_FILE_LINE_FOXTROT = f"foxtrot{NEWLINE}"
READ_FILE_LINES = (
    READ_FILE_LINE_ALPHA,
    READ_FILE_LINE_BRAVO,
    READ_FILE_LINE_CHARLIE,
    READ_FILE_LINE_DELTA,
    READ_FILE_LINE_ECHO,
    READ_FILE_LINE_FOXTROT,
)
READ_FILE_OFFSET = 2
READ_FILE_LIMIT = 2
READ_FILE_EXTRA_READS = 1
READ_FILE_EXPECTED_READS = READ_FILE_OFFSET + READ_FILE_LIMIT + READ_FILE_EXTRA_READS
READ_FILE_EXPECTED_LINE_NUMBER_START = 3
READ_FILE_EXPECTED_LINE_NUMBER_NEXT = 4
READ_FILE_EXPECTED_LINE_TEXT_START = "charlie"
READ_FILE_EXPECTED_LINE_TEXT_NEXT = "delta"
READ_FILE_UNEXPECTED_LINE_TEXT = "alpha"
READ_FILE_LAST_LINE = READ_FILE_OFFSET + READ_FILE_LIMIT

READLINES_CALLED_MESSAGE = "readlines should not be used for read_file"
READ_FILE_MODE = "r"

RIPGREP_BINARY_PATH = "/tmp/rg"
RIPGREP_PATTERN = "needle"
RIPGREP_SEARCH_PATH = "search-root"
RIPGREP_MATCH_LINE_NUMBER = 1
RIPGREP_STDOUT_TEXT = f"file.txt:{RIPGREP_MATCH_LINE_NUMBER}:{RIPGREP_PATTERN}"
RIPGREP_STDOUT_TEXT_WITH_NEWLINE = f"{RIPGREP_STDOUT_TEXT}{NEWLINE}"
RIPGREP_STDOUT_BYTES = RIPGREP_STDOUT_TEXT_WITH_NEWLINE.encode(
    ripgrep_module.PROCESS_OUTPUT_ENCODING
)
RIPGREP_EXPECTED_RESULTS = [RIPGREP_STDOUT_TEXT]
RIPGREP_EXPECTED_COMMAND = [RIPGREP_BINARY_PATH, RIPGREP_PATTERN, RIPGREP_SEARCH_PATH]
RIPGREP_TIMEOUT_SECONDS = 1
EMPTY_STDERR_BYTES = b""

GREP_MATCH_FILENAME = "match.txt"
GREP_MISS_FILENAME = "miss.txt"
GREP_MATCH_SUFFIX = " in haystack"
GREP_MATCH_LINE_TEXT = f"{RIPGREP_PATTERN}{GREP_MATCH_SUFFIX}"
GREP_MISS_LINE_TEXT = "nothing here"
GREP_MATCH_LINE_TEXT_WITH_NEWLINE = f"{GREP_MATCH_LINE_TEXT}{NEWLINE}"
GREP_MISS_LINE_TEXT_WITH_NEWLINE = f"{GREP_MISS_LINE_TEXT}{NEWLINE}"
GREP_EXPECTED_MATCH_COUNT = 1
GREP_MATCH_LINE_NUMBER = 1
GREP_OUTPUT_INDENT = "  "
GREP_FOUND_HEADER = f"Found {GREP_EXPECTED_MATCH_COUNT} matches"
GREP_EXPECTED_OUTPUT_LINE = f"{GREP_OUTPUT_INDENT}{GREP_MATCH_LINE_NUMBER}: {GREP_MATCH_LINE_TEXT}"
GREP_SEARCH_TYPE = "python"
GREP_CONTEXT_LINES = 0
GREP_MAX_RESULTS = 5
GREP_OUTPUT_MODE = "content"


def _write_lines(path: Path, lines: Iterable[str], encoding: str) -> None:
    content = EMPTY_TEXT.join(lines)
    path.write_text(content, encoding=encoding)


class _CountingReader:
    def __init__(self, lines: list[str]) -> None:
        self._lines = list(lines)
        self._index = 0
        self.readline_calls = 0

    def readline(self) -> str:
        self.readline_calls += 1
        if self._index >= len(self._lines):
            return EMPTY_TEXT
        line = self._lines[self._index]
        self._index += 1
        return line

    def readlines(self) -> list[str]:
        raise AssertionError(READLINES_CALLED_MESSAGE)

    def __enter__(self) -> _CountingReader:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        pass


class _CountingOpenFactory:
    def __init__(
        self,
        lines: Iterable[str],
        target_path: Path,
        real_open: Callable[..., object],
    ) -> None:
        self._lines = list(lines)
        self._target_path_text = str(target_path)
        self._real_open = real_open
        self.last_reader: _CountingReader | None = None

    def open(
        self,
        path: object,
        mode: str = READ_FILE_MODE,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
        closefd: bool = True,
        opener: object | None = None,
    ) -> object:
        path_text = str(path)
        if path_text == self._target_path_text:
            self.last_reader = _CountingReader(self._lines)
            return self.last_reader
        return self._real_open(
            path,
            mode,
            buffering,
            encoding,
            errors,
            newline,
            closefd,
            opener,
        )


class _FakeProcess:
    def __init__(self, stdout_bytes: bytes, returncode: int) -> None:
        self._stdout_bytes = stdout_bytes
        self.returncode = returncode
        self.killed = False

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout_bytes, EMPTY_STDERR_BYTES

    def kill(self) -> None:
        self.killed = True


class _CreateSubprocessRecorder:
    def __init__(self, process: _FakeProcess) -> None:
        self._process = process
        self.calls: list[list[str]] = []
        self.stdout_targets: list[int] = []
        self.stderr_targets: list[int] = []

    async def create(self, *cmd: str, stdout: int, stderr: int) -> _FakeProcess:
        self.calls.append(list(cmd))
        self.stdout_targets.append(stdout)
        self.stderr_targets.append(stderr)
        return self._process


def _format_expected_read_line(line_number: int, line_text: str) -> str:
    padded_number = str(line_number).zfill(LINE_NUMBER_PAD_WIDTH)
    return f"{padded_number}{LINE_NUMBER_SEPARATOR}{line_text}"


@pytest.mark.asyncio
async def test_read_file_reads_requested_range_without_readlines(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    file_path = tmp_path / READ_FILE_FILENAME
    _write_lines(file_path, READ_FILE_LINES, READ_FILE_ENCODING)

    open_factory = _CountingOpenFactory(READ_FILE_LINES, file_path, builtins.open)
    monkeypatch.setattr(builtins, "open", open_factory.open)

    result = await read_file_module.read_file(
        filepath=str(file_path),
        offset=READ_FILE_OFFSET,
        limit=READ_FILE_LIMIT,
    )

    reader = open_factory.last_reader
    assert reader is not None
    assert reader.readline_calls == READ_FILE_EXPECTED_READS

    expected_start_line = _format_expected_read_line(
        READ_FILE_EXPECTED_LINE_NUMBER_START,
        READ_FILE_EXPECTED_LINE_TEXT_START,
    )
    expected_next_line = _format_expected_read_line(
        READ_FILE_EXPECTED_LINE_NUMBER_NEXT,
        READ_FILE_EXPECTED_LINE_TEXT_NEXT,
    )
    expected_notice = MORE_LINES_MESSAGE.format(last_line=READ_FILE_LAST_LINE)

    assert READ_FILE_UNEXPECTED_LINE_TEXT not in result
    assert expected_start_line in result
    assert expected_next_line in result
    assert expected_notice in result


@pytest.mark.asyncio
async def test_ripgrep_search_uses_async_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    process = _FakeProcess(RIPGREP_STDOUT_BYTES, RIPGREP_MATCH_FOUND_EXIT_CODE)
    recorder = _CreateSubprocessRecorder(process)
    monkeypatch.setattr(ripgrep_module.asyncio, "create_subprocess_exec", recorder.create)

    executor = RipgrepExecutor(binary_path=Path(RIPGREP_BINARY_PATH))
    results = await executor.search(
        pattern=RIPGREP_PATTERN,
        path=RIPGREP_SEARCH_PATH,
        timeout=RIPGREP_TIMEOUT_SECONDS,
    )

    assert results == RIPGREP_EXPECTED_RESULTS
    assert recorder.calls == [RIPGREP_EXPECTED_COMMAND]
    assert recorder.stdout_targets == [ripgrep_module.asyncio.subprocess.PIPE]
    assert recorder.stderr_targets == [ripgrep_module.asyncio.subprocess.PIPE]


@pytest.mark.asyncio
async def test_ripgrep_search_returns_empty_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _run_timeout(cmd: list[str], timeout: int) -> tuple[int, str]:
        _ = cmd
        _ = timeout
        raise TimeoutError

    executor = RipgrepExecutor(binary_path=Path(RIPGREP_BINARY_PATH))
    monkeypatch.setattr(executor, "_run_ripgrep_command", _run_timeout)

    results = await executor.search(
        pattern=RIPGREP_PATTERN,
        path=RIPGREP_SEARCH_PATH,
        timeout=RIPGREP_TIMEOUT_SECONDS,
    )

    assert results == []


@pytest.mark.asyncio
async def test_grep_returns_results_for_fixture_directory(tmp_path: Path) -> None:
    match_path = tmp_path / GREP_MATCH_FILENAME
    miss_path = tmp_path / GREP_MISS_FILENAME
    _write_lines(match_path, [GREP_MATCH_LINE_TEXT_WITH_NEWLINE], READ_FILE_ENCODING)
    _write_lines(miss_path, [GREP_MISS_LINE_TEXT_WITH_NEWLINE], READ_FILE_ENCODING)

    output = await grep(
        pattern=RIPGREP_PATTERN,
        directory=str(tmp_path),
        search_type=GREP_SEARCH_TYPE,
        context_lines=GREP_CONTEXT_LINES,
        max_results=GREP_MAX_RESULTS,
        output_mode=GREP_OUTPUT_MODE,
    )

    match_path_text = str(match_path)
    assert GREP_FOUND_HEADER in output
    assert match_path_text in output
    assert GREP_EXPECTED_OUTPUT_LINE in output
