#!/bin/bash
set -euo pipefail

uv run pytest \
  tests/unit/ui/test_app_loading_indicator.py \
  tests/unit/ui/test_request_threading.py \
  tests/unit/ui/test_thinking_state.py \
  tests/integration/ui/test_submit_loading_lifecycle.py \
  -q
