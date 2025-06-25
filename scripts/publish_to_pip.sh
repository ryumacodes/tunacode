#!/usr/bin/env bash
# publish_to_pip.sh  —  build & upload with **automatic patch‑increment**
# -----------------------------------------------------------------------------
# 1. Find highest version among:
#       • the latest Git tag   (vX.Y.Z)
#       • the latest on PyPI   (tunacode-cli)
# 2. Increment patch → X.Y.(Z+1)
# 3. Tag, build, upload to **real** PyPI — no questions asked.
# -----------------------------------------------------------------------------

set -euo pipefail

PKG="tunacode-cli"           # PyPI package name

# ── repo root ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# ── emoji‑free logging helpers ─────────────────────────────────────────────
GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log(){ printf "%b\n" "${GREEN}==>${NC} $*"; }
die(){ printf "%b\n" "${RED}ERROR:${NC} $*" >&2; exit 1; }

# ── prerequisites -----------------------------------------------------------
for cmd in python3 git; do command -v $cmd >/dev/null || die "$cmd missing"; done
[[ -f ~/.pypirc ]] || die "~/.pypirc missing (should contain real‑PyPI token)"

# ── ensure clean working directory ------------------------------------------
if [[ -n $(git status --porcelain) ]]; then
    die "Working directory is not clean. Commit or stash changes before publishing."
fi

# Use virtual environment
VENV_PATH="venv"
[[ -d "$VENV_PATH" ]] || die "Virtual environment not found at $VENV_PATH"
PYTHON="$VENV_PATH/bin/python"
PIP="$VENV_PATH/bin/pip"

$PIP -q install build twine setuptools_scm packaging pytest black isort flake8 >/dev/null

# ── run tests and linting before publishing --------------------------------
log "Running linting checks"
if ! make lint-check; then
    die "Linting failed! Fix linting errors before publishing."
fi

log "Running tests"
if ! make test; then
    die "Tests failed! Fix failing tests before publishing."
fi

log "All checks passed!"

# ── cleanup -----------------------------------------------------------------
rm -rf dist build *.egg-info

# ── fetch latest PyPI version ----------------------------------------------
remote=$($PYTHON - "$PKG" <<'PY'
import json, sys, ssl, urllib.request, packaging.version as V
pkg=sys.argv[1]
try:
    data=json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{pkg}/json', context=ssl.create_default_context()))
    print(max(data['releases'], key=V.Version))
except Exception:
    print('0.0.0')
PY
)
log "Latest on PyPI  : $remote"

# ── fetch latest Git tag -----------------------------------------------------
git fetch --tags -q
local=$(git tag --sort=-v:refname | head -n1 | sed 's/^v//')
[[ -z $local ]] && local="0.0.0"
log "Latest Git tag  : $local"

# ── choose max(remote, local) & bump patch ----------------------------------
base=$($PYTHON - "$remote" "$local" <<'PY'
import sys, packaging.version as V
r,l=sys.argv[1:]
print(r if V.Version(r)>=V.Version(l) else l)
PY
)
IFS=. read -r MAJ MIN PAT <<<"$base"
VERSION="$MAJ.$MIN.$((PAT+1))"
log "Next version    : $VERSION"

# ── update pyproject.toml version -------------------------------------------
sed -i "s/^version = .*/version = \"$VERSION\"/" pyproject.toml

# ── update constants.py version ---------------------------------------------
sed -i "s/^APP_VERSION = .*/APP_VERSION = \"$VERSION\"/" src/tunacode/constants.py

# ── git add, commit, and push -----------------------------------------------
git add .
git commit -m "chore: bump version to $VERSION"

# ── tag & push --------------------------------------------------------------
git tag -m "Release v$VERSION" "v$VERSION"
git push --tags
git push

# ── build -------------------------------------------------------------------
log "Building wheel/sdist"; $PYTHON -m build

# ── upload ------------------------------------------------------------------
log "Uploading to PyPI"; $PYTHON -m twine upload -r pypi dist/*

log "🎉  $PKG $VERSION published on PyPI"






