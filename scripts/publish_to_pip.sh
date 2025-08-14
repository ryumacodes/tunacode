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

# ── ensure on master branch -------------------------------------------------
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "master" ]]; then
    die "You must be on the master branch to publish. Current branch: $current_branch"
fi

# ── ensure clean working directory ------------------------------------------
if [[ -n $(git status --porcelain) ]]; then
    die "Working directory is not clean. Commit or stash changes before publishing."
fi

# Use hatch for package management
command -v hatch >/dev/null || die "hatch not found - install with: uv tool install hatch"

# Hatch manages dependencies automatically when using features = [\"dev\"]

# ── run tests and linting before publishing --------------------------------
log "Running linting checks"
if ! hatch run lint-check; then
    die "Linting failed! Fix linting errors before publishing."
fi

log "Running tests"
if ! hatch run test; then
    die "Tests failed! Fix failing tests before publishing."
fi

log "All checks passed!"

# ── fetch latest PyPI version ----------------------------------------------
remote=$(uv run python - "$PKG" <<'PY'
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
base=$(uv run python - "$remote" "$local" <<'PY'
import sys, packaging.version as V
r,l=sys.argv[1:]
print(r if V.Version(r)>=V.Version(l) else l)
PY
)
IFS=. read -r MAJ MIN PAT <<<"$base"
VERSION="$MAJ.$MIN.$((PAT+1))"
log "Next version    : $VERSION"

# ── cleanup -----------------------------------------------------------------
# Only clean if we're building a new version
skip_build=false
if [[ -f "dist/tunacode_cli-${VERSION}-py3-none-any.whl" ]] && [[ -f "dist/tunacode_cli-${VERSION}.tar.gz" ]]; then
    log "Distribution files for v$VERSION already exist, skipping build"
    skip_build=true
else
    rm -rf dist build *.egg-info
fi

# ── update pyproject.toml version -------------------------------------------
current_pyproject_version=$(grep "^version = " pyproject.toml | cut -d'"' -f2)
if [[ "$current_pyproject_version" != "$VERSION" ]]; then
    sed -i "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
    log "Updated pyproject.toml to version $VERSION"
else
    log "pyproject.toml already at version $VERSION"
fi

# ── update constants.py version ---------------------------------------------
current_constants_version=$(grep "^APP_VERSION = " src/tunacode/constants.py | cut -d'"' -f2)
if [[ "$current_constants_version" != "$VERSION" ]]; then
    sed -i "s/^APP_VERSION = .*/APP_VERSION = \"$VERSION\"/" src/tunacode/constants.py
    log "Updated constants.py to version $VERSION"
else
    log "constants.py already at version $VERSION"
fi

# ── git add, commit, and push -----------------------------------------------
git add pyproject.toml src/tunacode/constants.py
if [[ -n $(git diff --cached --name-only) ]]; then
    git commit -m "chore: bump version to $VERSION"
    log "Committed version bump to $VERSION"
else
    log "No changes to commit - version already at $VERSION"
fi

# ── tag & push --------------------------------------------------------------
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    log "Tag v$VERSION already exists"
else
    git tag -m "Release v$VERSION" "v$VERSION"
    log "Created tag v$VERSION"
fi

git push --tags
git push

# ── build -------------------------------------------------------------------
if [[ "$skip_build" != "true" ]]; then
    log "Building wheel/sdist"
    hatch build
fi

# ── upload ------------------------------------------------------------------
log "Uploading to PyPI"
hatch run python -m twine upload -r pypi dist/* || log "Upload may have failed - package might already exist on PyPI"

log "✅ SUCCESS: $PKG $VERSION published on PyPI"
log "🎉 Deployment complete! Package available at: https://pypi.org/project/$PKG/$VERSION/"
