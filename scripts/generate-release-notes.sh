#!/usr/bin/env bash
# Generate release notes from git commits since last tag
# Uses conventional commit prefixes to categorize changes
set -euo pipefail

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -z "$LAST_TAG" ]]; then
    echo "No previous tag found, showing all commits"
    RANGE="HEAD"
else
    echo "Changes since $LAST_TAG:"
    RANGE="$LAST_TAG..HEAD"
fi

echo ""
echo "## [Unreleased]"
echo ""

# Categorize commits by prefix
declare -A CATEGORIES=(
    ["feat"]="### Added"
    ["fix"]="### Fixed"
    ["docs"]="### Documentation"
    ["refactor"]="### Changed"
    ["perf"]="### Performance"
    ["test"]="### Tests"
    ["chore"]="### Maintenance"
)

for prefix in feat fix docs refactor perf test chore; do
    commits=$(git log "$RANGE" --oneline --grep="^$prefix" --regexp-ignore-case 2>/dev/null | head -20 || true)
    if [[ -n "$commits" ]]; then
        echo "${CATEGORIES[$prefix]}"
        echo ""
        echo "$commits" | while read -r line; do
            # Extract commit message after hash
            msg=$(echo "$line" | sed 's/^[a-f0-9]* //')
            echo "- $msg"
        done
        echo ""
    fi
done

# Show uncategorized commits
other=$(git log "$RANGE" --oneline --invert-grep \
    --grep="^feat" --grep="^fix" --grep="^docs" \
    --grep="^refactor" --grep="^perf" --grep="^test" --grep="^chore" \
    2>/dev/null | head -10 || true)
if [[ -n "$other" ]]; then
    echo "### Other"
    echo ""
    echo "$other" | while read -r line; do
        msg=$(echo "$line" | sed 's/^[a-f0-9]* //')
        echo "- $msg"
    done
fi
