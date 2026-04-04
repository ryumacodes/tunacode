#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "usage: $0 <hook-type> [hook args...]" >&2
    exit 2
fi

HOOK_TYPE="$1"
shift

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK_DIR="$REPO_ROOT/.githooks"
EXPECTED_VENV="$REPO_ROOT/.venv"
PROJECT_PYTHON="$EXPECTED_VENV/bin/python"

cd "$REPO_ROOT"

# Ignore a stale shell venv activation from an old checkout path.
if [[ -n "${VIRTUAL_ENV:-}" && "$VIRTUAL_ENV" != "$EXPECTED_VENV" ]]; then
    unset VIRTUAL_ENV
fi

ARGS=(
    hook-impl
    --config=.pre-commit-config.yaml
    --hook-type="$HOOK_TYPE"
    --hook-dir "$HOOK_DIR"
    --
    "$@"
)

if [[ -x "$PROJECT_PYTHON" ]]; then
    exec "$PROJECT_PYTHON" -m pre_commit "${ARGS[@]}"
fi

cat >&2 <<EOF
Unable to run the $HOOK_TYPE hook.
Missing project hook runtime: $PROJECT_PYTHON
Run 'make install' to create the local .venv and reinstall git hooks.
EOF
exit 1
