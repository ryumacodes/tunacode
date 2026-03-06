---
title: Skills Package
summary: Discovery, validation, selection, caching, and prompt rendering for user-loaded `SKILL.md` modules.
read_when: Adding or debugging `/skills`, changing skill file validation, or tracing how loaded skills reach the system prompt.
depends_on: [infrastructure, core]
feeds_into: [core, ui]
---

# Skills Package

**Package:** `src/tunacode/skills/`

## What

The skills package is a **shared support subsystem**, not one of TunaCode's strict downward-only layers.
It lets users keep reusable operating instructions in filesystem-backed `SKILL.md` directories, then load those skills into a session with `/skills`.

At a high level it handles:

- discovering skill directories from project-local and user-global roots,
- loading `SKILL.md` metadata and full content,
- validating relative file references inside a skill,
- caching skill summaries and full bodies with mtime invalidation,
- attaching selected skills to session state, and
- rendering prompt blocks that make loaded skills active instructions for the agent.

## Skill directory contract

A skill lives in a directory shaped like this:

```text
.claude/skills/<skill-name>/
├── SKILL.md
└── other supporting files...
```

Discovery roots:

- local: `<project>/.claude/skills`
- global: `~/.claude/skills`

Discovery rules:

- each immediate child directory is treated as one skill,
- a skill only exists if the directory contains `SKILL.md`,
- duplicate names within one root are rejected case-insensitively, and
- local skills override global skills with the same name.

`SKILL.md` rules:

- modern skills should begin with YAML frontmatter delimited by `---`,
- frontmatter must define non-empty `name` and `description`,
- frontmatter `name` must exactly match the directory name,
- legacy skills without frontmatter are still accepted, and
- legacy descriptions are derived from the first non-empty body text or heading, else `"Legacy skill"`.

Reference validation rules:

- markdown links to relative files are collected from `SKILL.md`,
- URLs, anchors, absolute paths, `~` paths, and references containing spaces are ignored,
- direct relative paths must exist,
- single-segment references may be resolved recursively within the skill directory, and
- missing or ambiguous references raise `SkillReferenceError`.

## Key files

| File | Purpose |
|------|---------|
| `models.py` | Dataclasses and enums for skill state: `SkillSource`, `SkillSummary`, `LoadedSkill`, `SelectedSkill`. |
| `discovery.py` | Resolves local/global roots and discovers skill directories with deterministic local-over-global precedence. |
| `loader.py` | Reads `SKILL.md`, parses frontmatter, derives legacy descriptions, validates relative references, and lists related files in the skill directory. |
| `registry.py` | Public lookup API for the rest of the app: `list_skill_summaries()`, `get_skill_summary()`, `load_skill_by_name()`. Uses the infrastructure cache and logs invalid skills instead of crashing the catalog. |
| `search.py` | Deterministic search ranking for `/skills` and autocomplete. Prefers exact name, then prefix, then substring, then description matches. |
| `selection.py` | Session-level attach/clear/resolve helpers. Converts persisted skill names into `SelectedSkill` objects with full content and related file paths. |
| `prompting.py` | Renders `# Available Skills` and `# Selected Skills` prompt blocks and computes a fingerprint so skill changes invalidate the cached agent. |

## Integration points

### UI

The UI uses the skills package in three places:

- `ui/commands/skills.py` powers `/skills`, `/skills loaded`, `/skills clear`, and `/skills search <query>`.
- `ui/widgets/skills_autocomplete.py` suggests subcommands and skill names while typing.
- `ui/app.py` and `ui/context_panel.py` show loaded skill names in the context sidebar.

### Session state

Loaded skills are persisted as names only:

- `SessionState.selected_skill_names: list[str]`
- serialized by `StateManager.save_session()`
- validated by `_deserialize_selected_skill_names()` on load

That keeps the session payload small while allowing the latest skill content to be reloaded from disk.

### Agent prompt assembly

`core/agents/agent_components/agent_config.py` turns skills into prompt context:

1. `list_skill_summaries()` builds the catalog summary block.
2. `resolve_selected_skills(session.selected_skill_names)` loads active skills with absolute paths and full `SKILL.md` content.
3. `render_selected_skills_block()` emits a high-priority instruction block declaring loaded skills ACTIVE for the session.
4. `render_available_skills_block()` appends a lightweight catalog of discoverable skills.
5. `compute_skills_prompt_fingerprint()` feeds agent-version hashing so skill selection or content changes invalidate the cached agent.

Prompt order matters:

```text
system_prompt.md
+ AGENTS.md / tunacode context
+ # Selected Skills
+ # Available Skills
```

The selected-skills block is intentionally stronger than the available-skills block.
Loaded skills are treated as operating instructions, not optional reference material.

## How

### Discovery and load flow

```text
/skills
  -> list_skill_summaries()
  -> discover_skills()
  -> load_skill_summary()
  -> cache by skill_path mtime
```

### Attach flow

```text
/skills <exact-name>
  -> attach_skill(current_skill_names, requested_name)
  -> find discovered skill (local wins over global)
  -> load_skill(...) to validate the skill body
  -> persist canonical skill name into session.selected_skill_names
```

### Prompt injection flow

```text
selected_skill_names
  -> resolve_selected_skills()
  -> render_selected_skills_block()
  -> compute_skills_prompt_fingerprint()
  -> get_or_create_agent()
  -> agent system prompt includes active skill content and absolute paths
```

## Caching behavior

The package relies on `src/tunacode/infrastructure/cache/caches/skills.py`.

Two cached views are stored per skill file path:

- `summary` -> `SkillSummary`
- `loaded` -> `LoadedSkill`

Both use `MtimeStrategy`, so editing a `SKILL.md` file invalidates the cached entry automatically.

## Why this shape

- **Filesystem-backed skills** let teams keep reusable workflows near the codebase or in a user-wide toolbox.
- **Local-over-global precedence** allows project-specific overrides without renaming shared skills.
- **Validation at attach/load time** catches broken skill references before the model depends on them.
- **Name-only session persistence** avoids storing duplicated skill content in every saved session.
- **Prompt fingerprinting** ensures the agent cache stays correct when a skill is added, removed, or edited.
- **Search ranking by name first** keeps `/skills` predictable and fast for interactive use.
