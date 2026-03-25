#!/bin/bash
set -euo pipefail

uv run python -m py_compile \
  scripts/benchmarks/input_latency.py \
  src/tunacode/ui/app.py \
  src/tunacode/ui/thinking_state.py \
  src/tunacode/ui/widgets/chat.py

uv run python scripts/benchmarks/input_latency.py
