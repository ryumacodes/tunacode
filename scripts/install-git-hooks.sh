#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
TRACKED_HOOKS_DIR="$REPO_ROOT/.githooks"

mkdir -p "$HOOKS_DIR"

for hook_name in pre-commit pre-push; do
    hook_target="../../.githooks/$hook_name"
    hook_path="$HOOKS_DIR/$hook_name"
    rm -f "$hook_path"
    ln -s "$hook_target" "$hook_path"
done

echo "Installed repo-managed git hooks: pre-commit, pre-push"
