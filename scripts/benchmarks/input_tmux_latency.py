#!/usr/bin/env python3
"""Measure tmux-pane draft visibility latency during an active TunaCode request."""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import statistics
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock, patch

from tinyagent.agent_types import AssistantMessage, TextContent

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp

READY_TIMEOUT_SECONDS = float(os.environ.get("TUNACODE_BENCH_READY_TIMEOUT_S", "10.0"))
REQUEST_DURATION_SECONDS = float(os.environ.get("TUNACODE_BENCH_REQUEST_DURATION_S", "3.0"))
THINKING_CHUNK_INTERVAL_SECONDS = float(
    os.environ.get("TUNACODE_BENCH_THINKING_INTERVAL_S", "0.01")
)
THINKING_CHUNK_REPEAT = int(os.environ.get("TUNACODE_BENCH_THINKING_CHUNK_REPEAT", "50"))
ACTIVE_SETTLE_SECONDS = float(os.environ.get("TUNACODE_BENCH_ACTIVE_SETTLE_S", "0.5"))
POLL_INTERVAL_SECONDS = float(os.environ.get("TUNACODE_BENCH_POLL_INTERVAL_S", "0.025"))
PANE_CAPTURE_LINES = os.environ.get("TUNACODE_BENCH_CAPTURE_LINES", "-200")
MEASUREMENT_REPEATS = int(os.environ.get("TUNACODE_BENCH_REPEATS", "5"))
TMUX_TARGET_PANE = "0.0"
PROMPT_TEXT = "benchmark active request"


@dataclass(frozen=True)
class ScenarioStats:
    pane_p95_ms: float
    pane_median_ms: float
    pane_max_ms: float


async def _fake_process_request(
    *,
    thinking_callback: object | None = None,
    state_manager: StateManager,
    **_: object,
) -> None:
    deadline = time.perf_counter() + REQUEST_DURATION_SECONDS
    chunk_index = 0
    while time.perf_counter() < deadline:
        if thinking_callback is not None:
            chunk = (f"reasoning chunk {chunk_index} ") * THINKING_CHUNK_REPEAT
            await thinking_callback(chunk)
        chunk_index += 1
        await asyncio.sleep(THINKING_CHUNK_INTERVAL_SECONDS)

    state_manager.session.conversation.messages.append(
        AssistantMessage(content=[TextContent(text="benchmark response")])
    )


def _run_child() -> int:
    state_manager = StateManager()
    state_manager.save_session = AsyncMock(return_value=True)  # type: ignore[method-assign]
    app = TextualReplApp(state_manager=state_manager)
    with patch("tunacode.core.agents.main.process_request", new=_fake_process_request):
        app.run()
    return 0


def _run_tmux(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["tmux", *args], check=True, capture_output=True, text=True, env=env)


def _wait_for_file(path: Path, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"Timed out waiting for file: {path}")


def _capture_pane(session_name: str) -> str:
    result = _run_tmux(
        "capture-pane", "-pt", f"{session_name}:{TMUX_TARGET_PANE}", "-S", PANE_CAPTURE_LINES
    )
    return result.stdout


def _measure_pane_visibility(session_name: str, token: str) -> float:
    start = time.perf_counter()
    _run_tmux("send-keys", "-t", f"{session_name}:{TMUX_TARGET_PANE}", "-l", token)
    while True:
        pane_output = _capture_pane(session_name)
        if token in pane_output:
            return (time.perf_counter() - start) * 1000.0
        time.sleep(POLL_INTERVAL_SECONDS)


def _launch_session(tmpdir: Path) -> str:
    session_name = f"tunacode_bench_{uuid.uuid4().hex[:8]}"
    home_dir = tmpdir / "home"
    data_dir = tmpdir / "data"
    ready_file = tmpdir / "ready.txt"
    home_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    command = (
        f"cd {Path.cwd().as_posix()} && "
        f"source .venv/bin/activate && "
        f"uv run python {Path(__file__).as_posix()} --child"
    )
    _run_tmux(
        "new-session",
        "-d",
        "-s",
        session_name,
        "-e",
        f"HOME={home_dir}",
        "-e",
        f"XDG_DATA_HOME={data_dir}",
        "-e",
        f"TUNACODE_TEST_READY_FILE={ready_file}",
        "bash",
        "-lc",
        command,
    )
    _wait_for_file(ready_file, READY_TIMEOUT_SECONDS)
    return session_name


def _kill_session(session_name: str) -> None:
    subprocess.run(
        ["tmux", "kill-session", "-t", session_name],
        check=False,
        capture_output=True,
        text=True,
    )


def _run_idle_sample() -> float:
    with tempfile.TemporaryDirectory(prefix="tunacode-idle-bench-") as tmp:
        session_name = _launch_session(Path(tmp))
        try:
            token = f"IDLE_{uuid.uuid4().hex[:8]}"
            return _measure_pane_visibility(session_name, token)
        finally:
            _kill_session(session_name)


def _run_active_sample() -> float:
    with tempfile.TemporaryDirectory(prefix="tunacode-active-bench-") as tmp:
        session_name = _launch_session(Path(tmp))
        try:
            _run_tmux("send-keys", "-t", f"{session_name}:{TMUX_TARGET_PANE}", "-l", PROMPT_TEXT)
            _run_tmux("send-keys", "-t", f"{session_name}:{TMUX_TARGET_PANE}", "Enter")
            time.sleep(ACTIVE_SETTLE_SECONDS)
            token = f"ACTIVE_{uuid.uuid4().hex[:8]}"
            return _measure_pane_visibility(session_name, token)
        finally:
            _kill_session(session_name)


def _p95(values_ms: list[float]) -> float:
    ordered = sorted(values_ms)
    index = min(len(ordered) - 1, max(0, round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def _summarize(values_ms: list[float]) -> ScenarioStats:
    return ScenarioStats(
        pane_p95_ms=_p95(values_ms),
        pane_median_ms=statistics.median(values_ms),
        pane_max_ms=max(values_ms),
    )


def _run_parent() -> int:
    if shutil.which("tmux") is None:
        raise RuntimeError("tmux is required for this benchmark")

    idle_samples_ms: list[float] = []
    active_samples_ms: list[float] = []
    for _ in range(MEASUREMENT_REPEATS):
        idle_samples_ms.append(_run_idle_sample())
        active_samples_ms.append(_run_active_sample())

    idle_stats = _summarize(idle_samples_ms)
    active_stats = _summarize(active_samples_ms)
    active_idle_gap = active_stats.pane_p95_ms - idle_stats.pane_p95_ms

    print(f"idle pane p95: {idle_stats.pane_p95_ms:.3f} ms")
    print(f"active pane p95: {active_stats.pane_p95_ms:.3f} ms")
    print(f"active pane median: {active_stats.pane_median_ms:.3f} ms")
    print(f"active pane max: {active_stats.pane_max_ms:.3f} ms")
    print(f"active-idle pane gap: {active_idle_gap:.3f} ms")
    print(f"METRIC pane_p95={active_stats.pane_p95_ms:.3f}")
    print(f"METRIC pane_median={active_stats.pane_median_ms:.3f}")
    print(f"METRIC pane_max={active_stats.pane_max_ms:.3f}")
    print(f"METRIC idle_pane_p95={idle_stats.pane_p95_ms:.3f}")
    print(f"METRIC active_idle_pane_gap={active_idle_gap:.3f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args()
    if args.child:
        return _run_child()
    return _run_parent()


if __name__ == "__main__":
    raise SystemExit(main())
