# Smart Git Commit & Push

Stage all local changes, create a commit message that documents local vs remote diffs, commit, and push upstream.

## Execution Steps

### 1. Fetch & Diff
- Get current branch, fetch updates, and gather diff information:


### 2. Stage Changes
- assume the user wants ALL local chnages

### 3. Commit with Inline Diffs

Changes Summary:

Detailed Diffs (first 200 lines):

(All local changes staged and pushed by smart-commit)"`

### 4. Push

## Success Criteria

* Commit message contains file-level stats + truncated diff
* All local changes staged and committed
* Remote branch up to date with local

---

This command will:
- Include file-level summary
- Include inline diff (truncated for readability, 200 lines)
- Add a fallback note explaining that everything was staged/pushed
- Handle push conflicts with auto-rebase

The diff detail is truncated to 200 lines for readability.
