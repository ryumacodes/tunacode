---
title: "tinyagent 1.2.27 gil hotfix validation"
link: "tinyagent-1-2-27-gil-hotfix-validation"
type: debug_history
ontological_relations:
  - relates_to: [[input-latency-regression-probe]]
  - relates_to: [[input-latency-threaded-request-execution-log]]
tags: [debug_history, tinyagent, input-latency, gil, streaming, ui]
uuid: "6cb9ca15-b382-42a8-9cba-fb4279294811"
created_at: "2026-03-25T17:29:57Z"
---

## Purpose

Record the outcome of validating the emergency tinyagent hotfix release `tiny-agent-os==1.2.27`, which restores GIL release while the Rust `_alchemy` binding blocks on streamed events and final results.

This note captures:
- the exact package and binding installed into TunaCode's `.venv`
- the key before/after latency numbers
- what changed
- what did not change

## Installed Version And Binding

Repository dependency update:
- [pyproject.toml](/home/fabian/tunacode/pyproject.toml): `tiny-agent-os>=1.2.27`
- [uv.lock](/home/fabian/tunacode/uv.lock): `tiny-agent-os==1.2.27`

Fresh environment state after rebuild:
- distribution version: `1.2.27`
- binding path: `/home/fabian/tunacode/.venv/lib/python3.13/site-packages/tinyagent/_alchemy.abi3.so`
- file type: `ELF 64-bit LSB shared object, x86-64`
- BuildID: `cad9080a24c2c6f1af50a5c045ffd2c540a53e3e`
- sha256: `b005e97a847fe443ab829807a735cc6e13b4a106f88ccae8d8cc8921a2b652f3`

Verification command output used:

```text
dist_version=1.2.27
binding_path=/home/fabian/tunacode/.venv/lib/python3.13/site-packages/tinyagent/_alchemy.abi3.so
```

```text
.venv/lib/python3.13/site-packages/tinyagent/_alchemy.abi3.so: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, BuildID[sha1]=cad9080a24c2c6f1af50a5c045ffd2c540a53e3e, not stripped
b005e97a847fe443ab829807a735cc6e13b4a106f88ccae8d8cc8921a2b652f3  .venv/lib/python3.13/site-packages/tinyagent/_alchemy.abi3.so
```

## Pre-Hotfix Baseline

Before `1.2.27`, the key failure mode was:
- provider stream open returned quickly
- the first raw provider event landed about `1.1s` later
- the UI thread starved during that same window
- input felt sluggish and sometimes effectively unusable while the request was active

Representative pre-hotfix numbers from the earlier probe:
- `UI: delta_timer_drift ... 1077.6ms`
- `Stream: first_event ... since_start=1156.4ms`
- `Stream: provider_first_raw ... since_open=1161.3ms`
- `Bridge: ... backlog=435.5ms flush=0.6ms`

That combination strongly suggested GIL/scheduling starvation rather than TunaCode-side render cost.

## Post-Hotfix Validation

The user reran TunaCode with `/debug` enabled after upgrading to `tiny-agent-os==1.2.27` and reported that the UI "looks and feels better."

### Exact warm-request trace

```text
2026-03-25T17:28:37.268386+00:00 [DEBUG  ] [LIFECYCLE] Input: submit seq=2 raw_chars=14 normalized_chars=14 queue=0
2026-03-25T17:28:37.268537+00:00 [DEBUG  ] [LIFECYCLE] UI: loading show reason=submit queue=0
2026-03-25T17:28:37.278619+00:00 [DEBUG  ] [LIFECYCLE] Queue: seq=2 submit_to_enqueue=10.2ms queue=1
2026-03-25T17:28:37.279739+00:00 [DEBUG  ] [LIFECYCLE] Queue: seq=2 enqueue_to_start=1.1ms submit_to_start=11.4ms queue=0
2026-03-25T17:28:37.282272+00:00 [INFO   ] req=0843a5d6 Request started
2026-03-25T17:28:37.291969+00:00 [DEBUG  ] [LIFECYCLE] Init: pre_stream total=9.6ms
2026-03-25T17:28:37.293063+00:00 [DEBUG  ] [LIFECYCLE] Stream: start thread=124639714199104
2026-03-25T17:28:37.293607+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_open attempt=1/10 dur=0.3ms
2026-03-25T17:28:37.296895+00:00 [DEBUG  ] [LIFECYCLE] Stream: first_event type=AgentStartEvent since_start=3.8ms thread=124639714199104
2026-03-25T17:28:38.270876+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_first_raw type=start since_open=977.6ms since_response=977.3ms
2026-03-25T17:28:38.271205+00:00 [DEBUG  ] [LIFECYCLE] Stream: event_gap type=MessageStartEvent gap=974.1ms count=5
2026-03-25T17:28:38.720178+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_raw_gap type=thinking_delta gap=445.5ms count=4
2026-03-25T17:28:38.720479+00:00 [DEBUG  ] [LIFECYCLE] Stream: event_gap type=message_update/thinking_delta gap=445.7ms count=8
2026-03-25T17:28:39.160261+00:00 [DEBUG  ] [LIFECYCLE] Stream: provider_raw_gap type=text_delta gap=436.8ms count=8
2026-03-25T17:28:39.160720+00:00 [DEBUG  ] [LIFECYCLE] Stream: event_gap type=message_update/text_delta gap=437.2ms count=12
2026-03-25T17:28:39.174802+00:00 [DEBUG  ] [LIFECYCLE] Request complete (1877ms)
2026-03-25T17:28:39.178054+00:00 [DEBUG  ] [LIFECYCLE] UI: loading hide reason=request_complete visible=1909.5ms
2026-03-25T17:28:39.183793+00:00 [DEBUG  ] [LIFECYCLE] UI: request_trace seq=2 request=1904.1ms loading=1909.5ms submit_to_queue=10.2ms queue_to_start=1.1ms keypress_max=0.0ms keypress_slow=0/0 timer_drift_max=50.8ms bridge_backlog_max=59.1ms bridge_flush_max=0.7ms stream_cb_max=0.0ms thinking_cb_max=0.7ms
```

## What Changed

The important improvement is not that the provider got faster.

The important improvement is that TunaCode stayed responsive while the provider waited.

Post-hotfix:
- `timer_drift_max=50.8ms`
- `bridge_backlog_max=59.1ms`
- `bridge_flush_max=0.7ms`
- `keypress_slow=0/0`

Pre-hotfix representative run:
- `timer_drift_max=1077.6ms`
- `bridge_backlog_max=435.5ms`
- `bridge_flush_max=0.6ms`

Interpretation:
- provider-side first-raw latency is still about `978ms`
- but the UI no longer starves during that wait
- this is consistent with the tinyagent `1.2.27` release note: restoring GIL release while the Rust binding blocks

## What Did Not Change

The upstream model/provider still takes roughly `1s` before the first raw stream event appears in these runs:
- `Stream: provider_first_raw ... since_open=977.6ms`

That means:
- the hotfix did not eliminate network/provider latency
- the hotfix eliminated the Python scheduling/UI starvation that made that latency feel much worse

## Current Conclusion

The emergency tinyagent hotfix appears to address the actual product bug the user was feeling:
- TunaCode input stays responsive during an active request
- the giant `1s+` UI starvation spikes are gone
- the remaining delay is ordinary provider time-to-first-stream-event, not a local TUI freeze

## Recommended Follow-Up

- Keep the existing TunaCode debug probes for now until a few more real sessions confirm the improvement holds.
- If the UI remains stable across repeated real prompts, the next cleanup step is to decide which latency probes stay permanently and which should be removed or hidden behind `/debug`.
