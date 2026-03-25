#!/usr/bin/env python3
"""Measure editor keypress latency during an active TunaCode request."""

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

REQUEST_DURATION_S = float(os.environ.get("TUNACODE_BENCH_REQUEST_DURATION_S", "2.8"))
THINKING_CHUNK_INTERVAL_S = float(os.environ.get("TUNACODE_BENCH_THINKING_INTERVAL_S", "0.002"))
THINKING_CHUNK_REPEAT = int(os.environ.get("TUNACODE_BENCH_THINKING_CHUNK_REPEAT", "80"))
KEY_INTERVAL_S = float(os.environ.get("TUNACODE_BENCH_KEY_INTERVAL_S", "0.015"))
MEASUREMENT_REPEATS = int(os.environ.get("TUNACODE_BENCH_REPEATS", "5"))
KEY_SEQUENCE = os.environ.get("TUNACODE_BENCH_KEYS", "abcdefghijklmnopqrstuvwx")
SETTLE_DELAY_S = float(os.environ.get("TUNACODE_BENCH_SETTLE_DELAY_S", "0.2"))
START_TIMEOUT_S = float(os.environ.get("TUNACODE_BENCH_START_TIMEOUT_S", "1.5"))
STOP_TIMEOUT_S = float(os.environ.get("TUNACODE_BENCH_STOP_TIMEOUT_S", "5.0"))


@dataclass(frozen=True)
class ScenarioStats:
    median_ms: float
    p95_ms: float
    max_ms: float


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


async def _measure_keypresses(app: TextualReplApp, pilot: object) -> list[float]:
    latencies_ms: list[float] = []
    for key in KEY_SEQUENCE:
        before = time.perf_counter()
        await pilot.press(key)
        latencies_ms.append((time.perf_counter() - before) * 1000.0)
        await asyncio.sleep(KEY_INTERVAL_S)
    await asyncio.sleep(KEY_INTERVAL_S)
    return latencies_ms


async def _run_idle_sample() -> list[float]:
    state_manager = StateManager()
    state_manager.save_session = AsyncMock(return_value=True)  # type: ignore[method-assign]
    app = TextualReplApp(state_manager=state_manager)
    async with app.run_test() as pilot:
        await pilot.pause(SETTLE_DELAY_S)
        return await _measure_keypresses(app, pilot)


async def _run_active_sample() -> list[float]:
    state_manager = StateManager()
    state_manager.save_session = AsyncMock(return_value=True)  # type: ignore[method-assign]
    app = TextualReplApp(state_manager=state_manager)

    async with app.run_test() as pilot:
        with patch("tunacode.core.agents.main.process_request", new=_fake_process_request):
            app.editor.value = "benchmark prompt"
            await pilot.press("enter")
            await _wait_until(
                lambda: app.loading_indicator.has_class("active"), timeout=START_TIMEOUT_S
            )
            await pilot.pause(SETTLE_DELAY_S)
            latencies_ms = await _measure_keypresses(app, pilot)
            await _wait_until(
                lambda: not app.loading_indicator.has_class("active"),
                timeout=STOP_TIMEOUT_S,
            )
            return latencies_ms


def _summarize(samples_ms: list[float]) -> ScenarioStats:
    ordered = sorted(samples_ms)
    p95_index = min(len(ordered) - 1, max(0, round(0.95 * (len(ordered) - 1))))
    return ScenarioStats(
        median_ms=statistics.median(ordered),
        p95_ms=ordered[p95_index],
        max_ms=max(ordered),
    )


async def _main() -> int:
    idle_runs: list[ScenarioStats] = []
    active_runs: list[ScenarioStats] = []

    for _ in range(MEASUREMENT_REPEATS):
        idle_runs.append(_summarize(await _run_idle_sample()))
        active_runs.append(_summarize(await _run_active_sample()))

    idle_p95 = statistics.median(run.p95_ms for run in idle_runs)
    active_p95 = statistics.median(run.p95_ms for run in active_runs)
    active_median = statistics.median(run.median_ms for run in active_runs)
    active_max = statistics.median(run.max_ms for run in active_runs)
    regression_gap = active_p95 - idle_p95

    print(f"idle p95: {idle_p95:.3f} ms")
    print(f"active p95: {active_p95:.3f} ms")
    print(f"active median: {active_median:.3f} ms")
    print(f"active max: {active_max:.3f} ms")
    print(f"active-idle gap: {regression_gap:.3f} ms")
    print(f"METRIC input_p95={active_p95:.3f}")
    print(f"METRIC input_median={active_median:.3f}")
    print(f"METRIC input_max={active_max:.3f}")
    print(f"METRIC idle_p95={idle_p95:.3f}")
    print(f"METRIC active_idle_gap={regression_gap:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
