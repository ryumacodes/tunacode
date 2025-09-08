---
allowed-tools: View, Bash(git:*), Bash(jq:*), Bash(curl:*), Bash(gh:*), Bash(python:*), Bash(npm:*), Bash(kubectl:*), Bash(helm:*)
description: Synthesizes final documentation from Research → Plan → Execute → QA. Produces a clean developer-facing doc with context, decisions, and next steps.
writes-to: memory-bank/documentation
hard-guards:
  - Do not modify or rewrite research/plan/execute/QA artifacts
  - Produce a new synthesis doc only
  - No coding, fixes, or commits
---

# Documentation Synthesis (Final)

Create synthesized documentation for: $ARGUMENTS
(topic OR path to QA report)

## Initial Prompt
"I'm creating a **final documentation synthesis** that integrates Research, Plan, Execution, and QA. This is meant to prep the next developer to continue the work smoothly."

---

## Step 1 — Locate Inputs
- If `$ARGUMENTS` is a topic: find the newest chain in memory-bank (`research/`, `plan/`, `execute/`, `QA/`).
- If `$ARGUMENTS` is a path to QA report: trace its linked plan, log, report, and research.
- Always read FULLY (no offsets):
  - Research doc
  - Plan doc
  - Execution Log
  - Execution Report
  - QA Report

---

## Step 2 — Extract Metadata
- Topic, dates, owners from each doc.
- Commit ranges (from plan + execute).
- Verdict (from QA).
- Key tags, milestones, decisions.

---

## Step 3 — Write Synthesis Doc
Create `memory-bank/documentation/YYYY-MM-DD_HH-MM-SS_<topic>_synthesis.md`:

```markdown
---
title: "<topic> – Documentation Synthesis"
phase: Documentation
date: "{{timestamp}}"
owner: "{{agent_or_user}}"
sources:
  research: "memory-bank/research/<file>.md"
  plan: "memory-bank/plan/<file>.md"
  execute_log: "memory-bank/execute/<log>.md"
  execute_report: "memory-bank/execute/<report>.md"
  qa: "memory-bank/QA/<file>.md"
commit_range: "<start>..<end>"
verdict: "<QA verdict>"
---

# Documentation Synthesis – <topic>

## 0. Executive Summary
- One-paragraph overview of what was done and why
- QA verdict + top risks
- Next action for future dev

## 1. Context & Research
- Problem statement (from research)
- Key findings & gaps identified
- Linked references (permalinks, docs)

## 2. Plan Highlights
- Scope & assumptions
- Major milestones
- Deliverables & acceptance criteria
- Risks & mitigations

## 3. Execution Summary
- Commit range: `<start>..<end>`
- Work done by milestone
- Key tests, builds, deployments
- Deviations from plan (if any)
- Success criteria achieved vs missed

## 4. QA Findings
- Overall verdict: ✅ / ⚠️ / ❌
- Critical/high issues summary
- Smells & anti-patterns observed
- Ship conditions (if ⚠️)

## 5. Lessons Learned
- What worked well
- What caused friction
- Reusable patterns / gotchas

## 6. Next Steps for Developers
- Open follow-ups / tech debt
- Areas needing re-review
- Suggested tasks for next cycle
- Monitoring/observability items to watch

## 7. References
- Direct links to all artifacts
- GitHub permalinks (commits, files)
- Tickets/Issues


DEPLOY 3 paralel SUBAGENTS at most or one IF needed you can also you 1 or 2 use you best judgment

- codebase-analyzer to outline your code changes in relation to the codebase

- antipattern-sniffer any new code MUST be evaluted by this subagent

- context-synthesis a agent to gather context as needed
