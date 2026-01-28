---
title: Core File Filter
path: src/tunacode/core/file_filter.py
type: file
depth: 1
description: Core facade for UI file autocomplete filtering
exports: [FileFilter]
seams: [M]
---

# Core File Filter

## Purpose
Expose the file autocomplete filter at the core layer so UI widgets do not import utils directly.

## Key Classes

### FileFilter
Gitignore-aware file filtering with fuzzy prefix matching for autocomplete candidates.

## Integration Points

- **ui/widgets/file_autocomplete.py** - @-mention autocomplete
