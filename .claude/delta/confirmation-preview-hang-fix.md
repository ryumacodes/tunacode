---
title: Confirmation Preview Hang Fix for Large write_file Payloads
link: confirmation-preview-hang-fix
type: delta
ontological_relations:
  - relates_to: [[kb-claude-code-touchpoints]]
tags:
  - tui
  - confirmation
  - write-file
  - update-file
  - bug-fix
created_at: 2025-12-18T17:01:01Z
updated_at: 2025-12-18T17:01:01Z
uuid: 09b4492d-ce06-4850-8353-037004e8cf22
---

# Summary

Tool confirmation diff previews are now bounded (chars/lines/line-width) so a `write_file` call with very large single-line content (e.g., minified assets) can’t lock up the Textual UI.

# Root Cause

`ConfirmationRequestFactory` generated a creation diff for `write_file` by embedding the full line content; a large single-line payload produced multi‑MB `diff_content` which then froze Rich `Syntax` rendering in the confirmation panel.

# Changes

- Added bounded preview extraction in `src/tunacode/tools/authorization/requests.py`
- Applied the same preview bounding to `update_file` confirmation diffs
- Removed an import cycle in `src/tunacode/tools/authorization/handler.py` that made importing authorization modules order-dependent
- Added regression tests covering large single-line and many-line `write_file` payloads

# Behavioral Impact

- Confirmation previews remain responsive even for extremely large payloads.
- No change to tool execution behavior; only the confirmation preview text is truncated when needed.
