---
title: Core User Configuration
path: src/tunacode/core/user_configuration.py
type: file
depth: 1
description: Core facade for user configuration persistence
exports: [load_config_with_defaults, save_config]
seams: [M]
---

# Core User Configuration

## Purpose
Expose user configuration load/save helpers at the core layer so UI components do not import utils directly.

## Key Functions

### load_config_with_defaults
Loads user configuration from disk and merges it with defaults.

### save_config
Persists the active user configuration to disk.

## Integration Points

- **ui/commands/__init__.py** - model/theme commands
- **ui/screens/setup.py** - setup wizard save flow
