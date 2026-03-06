---
title: TunaCode Skills Feature Minimal Map
link: tunacode-skills-feature-minimal-map
type: metadata
path: memory-bank/research/2026-03-05_skills_feature_minimal_map.md
depth: 2
seams: [A]
ontological_relations:
  - relates_to: [[skills]]
  - affects: [[skill-discovery]]
  - affects: [[skill-selection]]
tags:
  - skills
  - tunacode
  - feature
  - lookup
  - local-global
created_at: 2026-03-05T18:30:45-06:00
updated_at: 2026-03-05T18:36:06-06:00
uuid: a1130167-c3d7-42d5-801d-45e44508b413
---

# Summary

This card is strictly about adding a skills feature to TunaCode. The feature must support two lookup roots:

1. project-local `.claude/skills/`
2. user-global `~/.claude/skills/`

Project-local skills override user-global skills when the same skill name exists in both places.

# Scope

This card covers:

- where TunaCode should look for skills
- the minimum behavior needed to discover and load skills
- the minimum code surface to add the feature cleanly
- the tests needed to prove the feature works

This card does not describe unrelated context-loading behavior.

# Required Lookup Behavior

## Skill roots

TunaCode should resolve skills from these roots, in this order:

1. `.claude/skills/`
2. `~/.claude/skills/`

## Skill directory shape

Each skill is a directory:

- `<root>/<skill-name>/SKILL.md`

Optional supporting files may sit beside `SKILL.md`, for example:

- `references/`
- `scripts/`
- `assets/`

## Precedence rule

If both roots contain the same `<skill-name>`:

- use the project-local skill
- do not merge local and global copies
- fail loudly on malformed local content rather than silently falling back

# Minimal Feature Slices

## 1. Discovery

Add a discovery step that:

- scans the local root if it exists
- scans the global root if it exists
- finds directories containing `SKILL.md`
- builds a registry keyed by skill name
- applies local-over-global precedence deterministically

## 2. Parsing

Add a loader that reads `SKILL.md` and extracts at minimum:

- skill name
- description
- absolute skill directory
- absolute `SKILL.md` path
- any referenced relative paths resolved against the skill directory
- only read the skill name and description at load, whe user call /skill it will popula like commandf but be /skill-skillname here then and only then wil we read the skill

## 3. Validation

Reject invalid skills loudly when:

- `SKILL.md` is missing
- frontmatter is malformed if required by the loader
- referenced relative files do not exist
- duplicate names collide inside the same root

## 4. Selection

Add a selection step that decides which skills are active for a request.

Minimum supported modes:

- explicit user request for a named skill
- project rule that requires a specific skill for a class of work

## 5. Runtime attachment

Once selected, skill instructions must be attached to the active TunaCode run in a deterministic order.

Minimum rule:

- attach only selected skills
- preserve a stable order by selected skill name
- show which skills were attached so the user can verify behavior

## 6. Caching and invalidation

Skill discovery and loaded skill content should be cacheable, but cache invalidation must occur when:

- `SKILL.md` changes
- a skill directory is added
- a skill directory is removed
- precedence changes because a local override appears or disappears

# Proposed Minimal Code Map

## New package

Add a dedicated package for skills:

- `src/tunacode/skills/models.py`
- `src/tunacode/skills/discovery.py`
- `src/tunacode/skills/loader.py`
- `src/tunacode/skills/registry.py`
- `src/tunacode/skills/selection.py`

## Suggested responsibilities

### `models.py`

Define explicit types for:

- `SkillSpec`
- `DiscoveredSkill`
- `SkillRegistry`
- `SelectedSkill`

### `discovery.py`

Own filesystem traversal for:

- local root discovery
- global root discovery
- duplicate detection
- precedence application

### `loader.py`

Own file loading for:

- `SKILL.md` reads
- relative path resolution against the skill directory
- fail-loud validation

### `registry.py`

Own high-level APIs such as:

- discover all skills
- get skill by name
- list available skills

### `selection.py`

Own request-time behavior such as:

- explicit skill selection
- required project skill selection
- stable ordering of selected skills

# Integration Points

## Core runtime

TunaCode needs one integration point where selected skills are attached to the current run.

That integration point should:

- accept already-selected `SelectedSkill` values
- avoid hidden filesystem access
- receive all inputs explicitly

## UI

The UI should show:

- available skills when relevant
- selected skills for the current run
- the source of each selected skill: `local` or `global`

## Configuration

If configuration is added, keep it minimal and explicit:

- local skills enabled by default
- global skills enabled by default
- optional hard disable for either root

# Test Map

Add tests for the feature in a dedicated skills test area.

## Discovery tests

- finds local skills
- finds global skills
- prefers local over global on name collision
- ignores directories without `SKILL.md`

## Loader tests

- reads valid `SKILL.md`
- resolves relative paths from the skill directory
- fails on missing referenced files
- fails on malformed skill structure

## Selection tests

- explicit named skill selection works
- required project skill selection works
- selected skills are attached in stable order

## Integration tests

- local-only environment works
- global-only environment works
- both roots present works
- local override replacing global works

# Current Repository State Relevant to the Feature

At the time of this scan:

- the repository has a `.claude/` directory
- the repository does not have a local `.claude/skills/` directory
- the environment does have a populated user-global `~/.claude/skills/` directory
- no TunaCode runtime skill subsystem exists yet in `src/`

# Minimal Conclusion

The TunaCode skills feature should be implemented as a dedicated subsystem with one clear rule:

- discover skills from both local and global roots
- prefer local over global by name
- load only selected skills
- fail loudly on invalid skill structure
- expose the selected skills to the user during the run
