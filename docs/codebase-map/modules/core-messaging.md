---
title: Core Messaging Facade
path: src/tunacode/core/messaging.py
type: file
depth: 1
description: Core-layer entry point for message content extraction
exports: [get_content]
seams: [M]
---

# Core Messaging Facade

## Purpose
Provide a core-layer entry point for extracting message content without importing utils directly from the UI.

## Key Functions

### get_content
Extracts the text content from a message payload using the canonical messaging adapter.

## Integration Points

- **ui/app.py** - replaying session messages
- **ui/headless/output.py** - resolving headless output
