---
title: Tools Layer
summary: Native tinyagent tool implementations and the helper modules they still depend on during the hard cutover.
read_when: Adding a tool, changing native tinyagent tool contracts, or tracing helper modules used by the active tools.
depends_on: [types, infrastructure, configuration]
feeds_into: [core]
---

# Tools Layer

**Package:** `src/tunacode/tools/`

## What

This layer exposes TunaCode's active native tinyagent tool surface directly. The supported tools are `bash`, `discover`, `read_file`, `hashline_edit`, `web_fetch`, and `write_file`.

Legacy decorator-based wrapping and XML prompt loading are intentionally removed during the hard cutover to native tinyagent tools.

## Current Modules

| File | Purpose |
|------|---------|
| `bash.py` | Native tinyagent shell execution tool. |
| `discover.py` | Native tinyagent repository discovery/search tool. |
| `read_file.py` | Native tinyagent file reader that returns hash-tagged lines. |
| `hashline_edit.py` | Native tinyagent edit tool for existing files with hash validation. |
| `web_fetch.py` | Native tinyagent public web fetch tool. |
| `write_file.py` | Native tinyagent file creation tool. |
| `hashline.py` | Hashline parsing and formatting helpers used by file tools. |
| `line_cache.py` | Line cache used to validate read-then-edit flows. |
| `ignore.py` | Ignore-rule access used by discovery and related helpers. |
| `ignore_manager.py` | Ignore stack implementation. |
| `utils/` | Shared discover, ripgrep, and formatting helpers still used by active tools. |
| `cache_accessors/` | Typed cache accessors still used by active tool helpers. |
| `lsp/` | LSP integration used for diagnostics and post-edit refresh behavior. |

## How

Tool registration is direct:
1. `agent_config.py::_build_tools()` imports native tool objects directly.
2. Each tool module defines its own parameter schema and `execute(tool_call_id, args, signal, on_update)` behavior.
3. Tool implementations construct `AgentToolResult` directly and return structured `content` and `details`.

## Why

The hard cutover removes the wrapper layer so the runtime and UI can preserve native tinyagent tool contracts end to end instead of flattening everything through a compatibility path.
