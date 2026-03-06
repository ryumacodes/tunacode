---
title: TunaCode Skills Module Map
link: tunacode-skills-module-map
type: metadata
path: memory-bank/research/2026-03-06_skills_module_map.md
depth: 2
seams: [A]
ontological_relations:
  - relates_to: [[skills]]
  - affects: [[skill-discovery]]
  - affects: [[skill-selection]]
  - affects: [[agent-prompt-injection]]
tags:
  - skills
  - tunacode
  - module-map
  - ui-commands
  - session-state
created_at: 2026-03-06T10:30:00-06:00
updated_at: 2026-03-06T10:30:00-06:00
uuid: 7f5c2d80-83d3-4f5b-a4cb-f0827f2144f9
---

# Summary

This card maps the currently implemented TunaCode skills subsystem.

It documents:

1. module/file structure
2. key symbols and line anchors
3. integration points across UI, session state, cache, and agent prompt assembly
4. command-to-prompt call chains

# Scope

This card covers:

- `src/tunacode/skills/*.py`
- `/skills` command and autocomplete wiring
- session persistence for selected skills
- agent prompt injection and version fingerprint linkage
- session inspector display of loaded skills

This card does not include implementation recommendations.

# Skills Module Structure

The skills package is:

- `src/tunacode/skills/__init__.py`
- `src/tunacode/skills/models.py`
- `src/tunacode/skills/discovery.py`
- `src/tunacode/skills/loader.py`
- `src/tunacode/skills/registry.py`
- `src/tunacode/skills/search.py`
- `src/tunacode/skills/selection.py`
- `src/tunacode/skills/prompting.py`

# Key Types and Symbols

## Domain types

- `src/tunacode/skills/models.py:8` - `SkillSource`
- `src/tunacode/skills/models.py:16` - `SkillSummary`
- `src/tunacode/skills/models.py:27` - `LoadedSkill`
- `src/tunacode/skills/models.py:40` - `SelectedSkill`

## Discovery

- `src/tunacode/skills/discovery.py:38` - `resolve_skill_roots`
- `src/tunacode/skills/discovery.py:59` - `discover_skills`
- `src/tunacode/skills/discovery.py:103` - `_discover_root_skills`
- `src/tunacode/skills/discovery.py:141` - `_merge_discovered_skills`

## Loading

- `src/tunacode/skills/loader.py:83` - `load_skill_summary`
- `src/tunacode/skills/loader.py:96` - `load_skill`
- `src/tunacode/skills/loader.py:116` - `list_skill_related_paths`
- `src/tunacode/skills/loader.py:260` - `_collect_referenced_paths`

## Registry and search

- `src/tunacode/skills/registry.py:16` - `list_skill_summaries`
- `src/tunacode/skills/registry.py:34` - `get_skill_summary`
- `src/tunacode/skills/registry.py:50` - `load_skill_by_name`
- `src/tunacode/skills/search.py:17` - `filter_skill_summaries`

## Selection and prompting

- `src/tunacode/skills/selection.py:28` - `attach_skill`
- `src/tunacode/skills/selection.py:67` - `resolve_selected_skills`
- `src/tunacode/skills/prompting.py:39` - `render_available_skills_block`
- `src/tunacode/skills/prompting.py:50` - `render_selected_skills_block`
- `src/tunacode/skills/prompting.py:96` - `compute_skills_prompt_fingerprint`

# Integration Points

## UI commands and routing

- Command registration: `src/tunacode/ui/commands/__init__.py:34`
- Command dispatch: `src/tunacode/ui/commands/__init__.py:57`
- Skills command implementation: `src/tunacode/ui/commands/skills.py:58`
- Editor submit event: `src/tunacode/ui/widgets/editor.py:127`
- App submit handler to command router: `src/tunacode/ui/app.py:329`
- Skills autocomplete prefix and candidates: `src/tunacode/ui/widgets/skills_autocomplete.py:13`, `src/tunacode/ui/widgets/skills_autocomplete.py:48`

## Session state persistence

- Session field declaration: `src/tunacode/core/session/state.py:64`
- Save serialization key: `src/tunacode/core/session/state.py:344`
- Load deserialization path: `src/tunacode/core/session/state.py:387`

## Agent prompt assembly

- Skills state builder: `src/tunacode/core/agents/agent_components/agent_config.py:439`
- Prompt assembly (selected + available blocks): `src/tunacode/core/agents/agent_components/agent_config.py:521`
- Skills fingerprint included in agent version input: `src/tunacode/core/agents/agent_components/agent_config.py:492`

## Cache linkage

- Skills cache registration: `src/tunacode/infrastructure/cache/caches/skills.py:21`
- Summary cache getter/setter: `src/tunacode/infrastructure/cache/caches/skills.py:24`, `src/tunacode/infrastructure/cache/caches/skills.py:36`
- Loaded-skill cache getter/setter: `src/tunacode/infrastructure/cache/caches/skills.py:47`, `src/tunacode/infrastructure/cache/caches/skills.py:59`

## Session inspector display

- Context panel skills field builder: `src/tunacode/ui/context_panel.py:158`
- Skill entries construction from `selected_skill_names`: `src/tunacode/ui/app.py:520`
- Context panel refresh updates skill field: `src/tunacode/ui/app.py:511`

# Call Chains

## Attach flow

1. `/skills <name>` enters `SkillsCommand.execute` at `src/tunacode/ui/commands/skills.py:58`
2. exact lookup + attach route via `_attach_or_search_skill` at `src/tunacode/ui/commands/skills.py:135`
3. selection transition in `attach_skill` at `src/tunacode/skills/selection.py:28`
4. session update at `src/tunacode/ui/commands/skills.py:163`
5. session persistence at `src/tunacode/ui/commands/skills.py:84`
6. inspector refresh at `src/tunacode/ui/commands/skills.py:164`

## Prompt injection flow

1. agent construction enters `get_or_create_agent` at `src/tunacode/core/agents/agent_components/agent_config.py:475`
2. skills prompt state computed in `_build_skills_prompt_state` at `src/tunacode/core/agents/agent_components/agent_config.py:439`
3. selected and available blocks appended in `system_prompt` at `src/tunacode/core/agents/agent_components/agent_config.py:521`
4. resulting prompt set on agent at `src/tunacode/core/agents/agent_components/agent_config.py:559`

# Dependency Map

## Imports in `/skills` command

`src/tunacode/ui/commands/skills.py` imports:

- `tunacode.skills.loader.SkillLoadError`
- `tunacode.skills.models.SkillSummary`
- `tunacode.skills.registry.get_skill_summary`
- `tunacode.skills.registry.list_skill_summaries`
- `tunacode.skills.search.filter_skill_summaries`
- `tunacode.skills.selection.attach_skill`
- `tunacode.skills.selection.clear_attached_skills`

## Imports in agent config (skills slice)

`src/tunacode/core/agents/agent_components/agent_config.py` imports:

- `tunacode.skills.models.SelectedSkill`
- `tunacode.skills.prompting.compute_skills_prompt_fingerprint`
- `tunacode.skills.prompting.render_available_skills_block`
- `tunacode.skills.prompting.render_selected_skills_block`
- `tunacode.skills.registry.list_skill_summaries`
- `tunacode.skills.selection.resolve_selected_skills`

# Test Coverage Map

- Skills prompt injection test file: `tests/unit/core/test_agent_skills_prompt_injection.py`
- Main integration assertion for selected-skill prompt block: `tests/unit/core/test_agent_skills_prompt_injection.py:40`
- Assertions for absolute path rendering and selected-before-available ordering: `tests/unit/core/test_agent_skills_prompt_injection.py:76`

# Observed Structural Facts

- Name resolution by case-insensitive scan exists in both:
  - `src/tunacode/skills/selection.py:11`
  - `src/tunacode/skills/registry.py:66`
- Selection path directly calls `load_skill` in:
  - `src/tunacode/skills/selection.py:58`
  - `src/tunacode/skills/selection.py:86`
- Registry contains separate cache-backed loaded-skill path in:
  - `src/tunacode/skills/registry.py:101`
