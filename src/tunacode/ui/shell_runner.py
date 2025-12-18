"""Async shell command runner for the Textual TUI."""

from __future__ import annotations

import asyncio
import signal
import subprocess
from dataclasses import dataclass
from typing import Protocol

from rich.text import Text

SHELL_COMMAND_TIMEOUT_SECONDS: float = 30.0
SHELL_COMMAND_CANCEL_GRACE_SECONDS: float = 0.5
SHELL_COMMAND_USAGE_TEXT = "Usage: !<command>"
SHELL_OUTPUT_ENCODING = "utf-8"
SHELL_CANCEL_SIGNAL = signal.SIGINT


class ShellRunnerHost(Protocol):
    def notify(self, message: str, severity: str = "information") -> None: ...

    def write_shell_output(self, renderable: Text) -> None: ...

    def shell_status_running(self) -> None: ...

    def shell_status_last(self) -> None: ...


@dataclass
class ShellRunner:
    host: ShellRunnerHost

    _task: asyncio.Task[None] | None = None
    _process: asyncio.subprocess.Process | None = None

    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self, raw_cmd: str) -> None:
        cmd = raw_cmd.strip()
        if not cmd:
            self.host.notify(SHELL_COMMAND_USAGE_TEXT, severity="warning")
            return

        if self.is_running():
            self.host.notify(
                "Shell command already running (! or Esc to cancel)",
                severity="warning",
            )
            return

        self._task = asyncio.create_task(self._run(cmd))
        self._task.add_done_callback(self._on_done)

    def cancel(self) -> None:
        if not self.is_running():
            return

        process = self._process
        if process is None:
            assert self._task is not None
            self._task.cancel()
            return

        try:
            process.send_signal(SHELL_CANCEL_SIGNAL)
        except ProcessLookupError:
            assert self._task is not None
            self._task.cancel()
            return

        assert self._task is not None
        self._task.cancel()

    def _on_done(self, task: asyncio.Task[None]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            self.host.write_shell_output(Text(f"Shell error: {exc}"))

    async def _wait_or_kill_process(self, process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return

        try:
            await asyncio.wait_for(process.wait(), timeout=SHELL_COMMAND_CANCEL_GRACE_SECONDS)
        except TimeoutError:
            process.kill()
            await process.wait()

    async def _run(self, cmd: str) -> None:
        self.host.shell_status_running()
        self.host.notify(f"Running: {cmd}")

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        self._process = process

        try:
            stdout, _ = await asyncio.wait_for(
                process.communicate(),
                timeout=SHELL_COMMAND_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            self.host.notify("Command timed out", severity="error")
            return
        except asyncio.CancelledError:
            await self._wait_or_kill_process(process)
            self.host.notify("Shell command cancelled", severity="warning")
            raise
        finally:
            self._process = None
            self.host.shell_status_last()

        output = (stdout or b"").decode(SHELL_OUTPUT_ENCODING, errors="replace").rstrip()
        if output:
            self.host.write_shell_output(Text(output))

        if process.returncode is not None and process.returncode != 0:
            self.host.notify(f"Exit code: {process.returncode}", severity="warning")
