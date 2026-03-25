#!/usr/bin/env python3
"""Measure editor paint latency during an active TunaCode request."""

from __future__ import annotations

import asyncio
import os
import statistics
import time
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from tinyagent.agent_types import AssistantMessage, TextContent

from tunacode.core.session import StateManager

from tunacode.ui.app import TextualReplApp
from tunacode.ui.widgets.editor import Editor

REQUEST_DURATION_S = float(os.environ.get("TUNACODE_BENCH_REQUEST_DURATION_S", "2.8"))
THINKING_CHUNK_INTERVAL_S = float(os.environ.get("TUNACODE_BENCH_THINKING_INTERVAL_S", "0.002"))
THINKING_CHUNK_REPEAT = int(os.environ.get("TUNACODE_BENCH_THINKING_CHUNK_REPEAT", "80"))
KEY_INTERVAL_S = float(os.environ.get("TUNACODE_BENCH_KEY_INTERVAL_S", "0.015"))
MEASUREMENT_REPEATS = int(os.environ.get("TUNACODE_BENCH_REPEATS", "5"))
KEY_SEQUENCE = os.environ.get("TUNACODE_BENCH_KEYS", "abcdefghijklmnopqrstuvwx")
SETTLE_DELAY_S = float(os.environ.get("TUNACODE_BENCH_SETTLE_DELAY_S", "0.2"))
START_TIMEOUT_S = float(os.environ.get("TUNACODE_BENCH_START_TIMEOUT_S", "1.5"))
STOP_TIMEOUT_S = float(os.environ.get("TUNACODE_BENCH_STOP_TIMEOUT_S", "5.0"))
PAINT_TIMEOUT_S = float(os.environ.get("TUNACODE_BENCH_PAINT_TIMEOUT_S", "1.0"))


@dataclass(frozen=True)
class ScenarioStats:
    paint_p95_ms: float
    paint_median_ms: float
    press_return_p95_ms: float
    paint_after_return_p95_ms: float


@dataclass
class RenderTracker:
    expected_value: str | None = None
    rendered_at: float | None = None


async def _wait_until(predicate: object, *, timeout: float, step: float = 0.01) -> None:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if callable(predicate) and predicate():
            return
        await asyncio.sleep(step)
    raise RuntimeError(f"Condition not met within {timeout:.2f}s")


async def _fake_process_request(
    *,
    thinking_callback: object | None = None,
    state_manager: StateManager,
    **_: object,
) -> None:
    deadline = time.perf_counter() + REQUEST_DURATION_S
    chunk_index = 0
    while time.perf_counter() < deadline:
        if thinking_callback is not None:
            chunk = (f"reasoning chunk {chunk_index} ") * THINKING_CHUNK_REPEAT
            await thinking_callback(chunk)
        chunk_index += 1
        await asyncio.sleep(THINKING_CHUNK_INTERVAL_S)

    state_manager.session.conversation.messages.append(
        AssistantMessage(content=[TextContent(text="benchmark response")])
    )


def _instrument_editor_render(tracker: RenderTracker):
    original_render_line = Editor.render_line

    def _patched_render_line(self: Editor, y: int):
        result = original_render_line(self, y)
        if (
            tracker.expected_value is not None
            and tracker.rendered_at is None
            and self.value == tracker.expected_value
        ):
            tracker.rendered_at = time.perf_counter()
        return result

    return patch.object(Editor, "render_line", _patched_render_line)


async def _measure_keypresses(
    app: TextualReplApp, pilot: object, tracker: RenderTracker
) -> tuple[list[float], list[float], list[float]]:
    paint_latencies_ms: list[float] = []
    press_return_latencies_ms: list[float] = []
    paint_after_return_ms: list[float] = []

    for key in KEY_SEQUENCE:
        expected_value = app.editor.value + key
        tracker.expected_value = expected_value
        tracker.rendered_at = None
        before = time.perf_counter()
        await pilot.press(key)
        after_press = time.perf_counter()
        await _wait_until(
            lambda: tracker.rendered_at is not None, timeout=PAINT_TIMEOUT_S, step=0.001
        )
        assert tracker.rendered_at is not None
        paint_ms = (tracker.rendered_at - before) * 1000.0
        press_return_ms = (after_press - before) * 1000.0
        paint_latencies_ms.append(paint_ms)
        press_return_latencies_ms.append(press_return_ms)
        paint_after_return_ms.append(max(0.0, paint_ms - press_return_ms))
        await asyncio.sleep(KEY_INTERVAL_S)

    await asyncio.sleep(KEY_INTERVAL_S)
    tracker.expected_value = None
    tracker.rendered_at = None
    return paint_latencies_ms, press_return_latencies_ms, paint_after_return_ms


async def _run_idle_sample() -> tuple[list[float], list[float], list[float]]:
    state_manager = StateManager()
    state_manager.save_session = AsyncMock(return_value=True)  # type: ignore[method-assign]
    app = TextualReplApp(state_manager=state_manager)
    tracker = RenderTracker()

    with _instrument_editor_render(tracker):
        async with app.run_test() as pilot:
            await pilot.pause(SETTLE_DELAY_S)
            return await _measure_keypresses(app, pilot, tracker)


async def _run_active_sample() -> tuple[list[float], list[float], list[float]]:
    state_manager = StateManager()
    state_manager.save_session = AsyncMock(return_value=True)  # type: ignore[method-assign]
    app = TextualReplApp(state_manager=state_manager)
    tracker = RenderTracker()

    with _instrument_editor_render(tracker):
        async with app.run_test() as pilot:
            with patch("tunacode.core.agents.main.process_request", new=_fake_process_request):
                app.editor.value = "benchmark prompt"
                await pilot.press("enter")
                await _wait_until(
                    lambda: app.loading_indicator.has_class("active"), timeout=START_TIMEOUT_S
                )
                await pilot.pause(SETTLE_DELAY_S)
                metrics = await _measure_keypresses(app, pilot, tracker)
                await _wait_until(
                    lambda: not app.loading_indicator.has_class("active"),
                    timeout=STOP_TIMEOUT_S,
                )
                return metrics


def _p95(values_ms: list[float]) -> float:
    ordered = sorted(values_ms)
    index = min(len(ordered) - 1, max(0, round(0.95 * (len(ordered) - 1))))
    return ordered[index]


def _summarize(
    paint_ms: list[float],
    press_return_ms: list[float],
    paint_after_return_ms: list[float],
) -> ScenarioStats:
    return ScenarioStats(
        paint_p95_ms=_p95(paint_ms),
        paint_median_ms=statistics.median(paint_ms),
        press_return_p95_ms=_p95(press_return_ms),
        paint_after_return_p95_ms=_p95(paint_after_return_ms),
    )


async def _main() -> int:
    idle_runs: list[ScenarioStats] = []
    active_runs: list[ScenarioStats] = []

    for _ in range(MEASUREMENT_REPEATS):
        idle_runs.append(_summarize(*await _run_idle_sample()))
        active_runs.append(_summarize(*await _run_active_sample()))

    idle_paint_p95 = statistics.median(run.paint_p95_ms for run in idle_runs)
    active_paint_p95 = statistics.median(run.paint_p95_ms for run in active_runs)
    active_paint_median = statistics.median(run.paint_median_ms for run in active_runs)
    active_press_return_p95 = statistics.median(run.press_return_p95_ms for run in active_runs)
    active_paint_after_return_p95 = statistics.median(
        run.paint_after_return_p95_ms for run in active_runs
    )
    active_idle_gap = active_paint_p95 - idle_paint_p95

    print(f"idle paint p95: {idle_paint_p95:.3f} ms")
    print(f"active paint p95: {active_paint_p95:.3f} ms")
    print(f"active paint median: {active_paint_median:.3f} ms")
    print(f"active press-return p95: {active_press_return_p95:.3f} ms")
    print(f"active paint-after-return p95: {active_paint_after_return_p95:.3f} ms")
    print(f"active-idle paint gap: {active_idle_gap:.3f} ms")
    print(f"METRIC paint_p95={active_paint_p95:.3f}")
    print(f"METRIC paint_median={active_paint_median:.3f}")
    print(f"METRIC press_return_p95={active_press_return_p95:.3f}")
    print(f"METRIC paint_after_return_p95={active_paint_after_return_p95:.3f}")
    print(f"METRIC idle_paint_p95={idle_paint_p95:.3f}")
    print(f"METRIC active_idle_paint_gap={active_idle_gap:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
