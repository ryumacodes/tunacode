---
title: "prompt versioning mapping"
link: "prompt-versioning-map"
type: research
ontological_relations:
  - relates_to: [[PROMPT-MODIFIERS]]
tags: [research, prompts, versioning]
uuid: "c279aa8c-4dad-4d13-af30-1be7afa359bb"
created_at: "2026-03-21T14:07:39Z"
---

## Structure
- `src/tunacode/prompts/versioning.py` implements prompt hash computation and aggregate fingerprint building.
- `src/tunacode/infrastructure/cache/caches/prompt_version_cache.py` registers and stores mtime-invalidated `PromptVersion` objects.
- `src/tunacode/prompts/version_display.py` formats and prints combined version objects.
- `src/tunacode/types/canonical.py` defines `PromptVersion` and `AgentPromptVersions` dataclasses.
- `src/tunacode/core/agents/agent_components/agent_config.py` loads prompt files, computes prompt version snapshots, stores/attaches them on each created agent, and logs hashes.
- `src/tunacode/tools/decorators.py` computes optional prompt version for each tool’s XML description file and sets `agent_tool.prompt_version`.
- `tests/unit/prompts/test_versioning.py` validates version-computation functions.
- `tests/unit/core/test_agent_cache_abort.py` and related agent unit tests stub `AgentPromptVersions` when patching agent creation.
- `tests/integration/core/test_mtime_caches_end_to_end.py` and `tests/integration/core/test_minimax_execution_path.py` assert current return-shape and behavior from context/system prompt loaders.
- `docs/modules/prompts/versioning.md` is a standalone documentation page for the subsystem.

## Core data model
- `PromptVersion` fields currently are at `src/tunacode/types/canonical.py:317-348`:
  - `source_path`, `content_hash`, `mtime`, `computed_at`, `length`.
- `AgentPromptVersions` at `src/tunacode/types/canonical.py:336-347`:
  - `system_prompt`, `tunacode_context`, `tool_prompts`, `fingerprint`, `computed_at`.

## Prompt versioning call flow
- `agent_config.load_system_prompt()` reads `src/tunacode/prompts/system_prompt.md` and calls `get_or_compute_prompt_version()` on that path (`agent_config.py:132-140`).
- `agent_config.load_tunacode_context()` reads/caches `AGENTS.md` via `context_cache.get_context()` and calls `get_or_compute_prompt_version()` on that path (`agent_config.py:143-149`).
- `get_or_create_agent()` calls both loaders, builds tools, then calls `compute_agent_prompt_versions()` with system/context/tool paths (`agent_config.py:517-521`).
- `compute_agent_prompt_versions()` calls `compute_prompt_version()` for each configured prompt path, builds per-source `PromptVersion`s, then hashes `system:`, `context:`, and sorted `tool:` entries into `fingerprint` (`prompts/versioning.py:93-152`).
- Tool paths are discovered by `_collect_tool_prompt_paths()` via `get_xml_prompt_path()` in the tool list (`agent_config.py:436-442`).
- `_augment_prompt_versions_with_skills()` concatenates `AgentPromptVersions.fingerprint` with the skills fingerprint to produce a second version-hash (`agent_config.py:401-415`).
- The result is stored as `agent.prompt_versions` on the tinyagent instance and logged (`agent_config.py:538-548`).
- `to_tinyagent_tool()` also loads `prompt_version` from each XML prompt path and stores `agent_tool.prompt_version` (`tools/decorators.py:170-185, 228-229`).

## Caching mechanics for prompt versions
- `versioning.compute_prompt_version()` computes `sha256(content) + mtime + length` and returns `PromptVersion`.
- `versioning.get_or_compute_prompt_version()` first checks cache via `get_prompt_version()`, then writes cache via `set_prompt_version()` on miss (`prompts/versioning.py:60-90`).
- `prompt_version_cache` uses `MtimeStrategy` and path-based keys (`prompt_version_cache.py:21-23, 26-54, 57-71`).

## Files and exact references
- `src/tunacode/prompts/versioning.py`: `compute_prompt_version` (L22-57), `get_or_compute_prompt_version` (L60-90), `compute_agent_prompt_versions` (L93-152), `versions_equal` (L155-172), `agent_versions_equal` (L174-193).
- `src/tunacode/prompts/version_display.py`: formatting + print helpers only; module-level usage only inside module (`version_display.py:18-131`).
- `src/tunacode/infrastructure/cache/caches/prompt_version_cache.py`: cache registration and helpers (`L16-89`).
- `src/tunacode/core/agents/agent_components/agent_config.py`: imports (`L40-53`), system/context return-tuple loaders (`L132-149`), versioned logging (`L464-477`), version-collection pipeline (`L517-549`).
- `src/tunacode/tools/decorators.py`: optional tool-level version attach (`L170-185`, `L228-230`).

## Dependency and test map
- `prompt_versioning` symbols are consumed by:
  - production: `core/agent_config.py` and `tools/decorators.py`.
  - tests: `tests/unit/prompts/test_versioning.py` and `tests/unit/core/test_agent_cache_abort.py` (`AgentPromptVersions` typing), plus loader return-shape patches in:
    - `tests/unit/core/test_agent_skills_prompt_injection.py:59-68`
    - `tests/integration/core/test_minimax_execution_path.py:76-80`
    - `tests/integration/core/test_mtime_caches_end_to_end.py:42-57`.
- No production call sites read `agent.prompt_versions` or `agent_tool.prompt_version`.
- No production call sites import `clear_prompt_versions` from cache accessor.

## Observed docs and metadata
- `docs/modules/prompts/versioning.md` documents this behavior as a standalone subsystem; line references include architecture, data structures, logging, and integration examples.
- `CHANGELOG.md` notes the prompt-versioning feature as added in `0.1.79` (`CHANGELOG.md:160`).
- `docs/modules/core/core.md` mentions prompt version aggregation via `_augment_prompt_versions_with_skills()` in the agent config summary block.
