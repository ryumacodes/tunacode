# .claude

Developer and agent-specific documentation for tunacode.

## Directory Structure

```
.claude/
├── agents/                    # Agent definitions
│   ├── bug-context-analyzer.md
│   ├── code-synthesis-analyzer.md
│   ├── documentation-synthesis-qa.md
│   ├── expert-debugger.md
│   ├── phased-task-processor.md
│   ├── prompt-engineer.md
│   ├── rapid-code-synthesis-qa.md
│   └── tech-docs-maintainer.md
├── commands/                  # Slash commands
│   ├── deploy.md
│   ├── github-issue.md
│   ├── smells.md
│   ├── work.md
│   └── workflow.md
├── delta/                     # Version diffs and changes
│   ├── 2025-01-05-baseline.yml
│   ├── fix-text-alignment-layout-task3.md
│   ├── task4_ui_formatting_fix.md
│   └── v0.0.53_to_v0.0.54.diff
├── development/               # Development setup and guides
│   ├── model-updates-2025.md # Latest model versions
│   ├── slash-commands.md     # Slash command system overview
│   └── uv-hatch-setup.md     # UV + Hatch configuration guide
├── metadata/                  # Project metadata
│   ├── components.yml
│   └── hotspots.txt
├── patterns/                  # Code patterns
│   └── json_retry_implementation.md
├── qa/                        # QA test definitions
│   ├── fix-agent-errors.yml
│   ├── fix-publish-script.yml
│   └── fix-runtime-warnings.yml
├── scratchpad/               # Working notes
│   ├── active/              # Current tasks
│   ├── agents/              # Agent-specific notes
│   ├── archived/            # Completed tasks
│   ├── locks/               # Lock files
│   └── shared/              # Shared resources
├── anchors.json              # Memory anchors
├── MEMORY_ANCHOR_SPEC.md     # Anchor specifications
├── NEXT_PR_RULES.md          # PR guidelines
└── settings.local.json       # Local settings
```

## Purpose

Developer-specific documentation, agent configurations, and internal workflows
