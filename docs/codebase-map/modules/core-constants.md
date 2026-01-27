---
title: Core Constants Facade
path: src/tunacode/core/constants.py
type: file
depth: 1
description: Core-layer access to shared constants and theme builders for the UI
exports: [APP_NAME, APP_VERSION, ENV_OPENAI_BASE_URL, UI_COLORS, build_tunacode_theme, build_nextstep_theme]
seams: [M]
---

# Core Constants Facade

## Purpose
Expose shared constants and theme helpers at the core layer so UI modules do not import `tunacode.constants` directly.

## Key Exports

### UI and Rendering Constants
Includes UI_COLORS, panel sizing constants, and viewport thresholds used across renderers.

### Theme Builders
build_tunacode_theme and build_nextstep_theme for registering Textual themes.

### Application Metadata
APP_NAME, APP_VERSION, and ENV_OPENAI_BASE_URL for UI display and configuration.

## Integration Points

- **ui/app.py** - theme registration and panel sizing
- **ui/main.py** - base URL overrides and version display
- **ui/renderers/** - UI colors and layout constants
- **ui/widgets/resource_bar.py** - cost formatting
