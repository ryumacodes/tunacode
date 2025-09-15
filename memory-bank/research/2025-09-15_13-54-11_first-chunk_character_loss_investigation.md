---
title: "Research – First-Chunk Character Loss Investigation"
date: "2025-09-15"
owner: "context-engineer:research"
phase: "Research"
git_commit: "d5effd6"
tags: ["streaming", "ui", "character-loss", "race-conditions", "debugging"]
---

# Research – First-Chunk Character Loss Investigation

**Date:** 2025-09-15
**Owner:** context-engineer:research
**Phase:** Research

## Goal
Investigate and identify the root cause of first-character loss in TunaCode's streaming display where messages like "TUNACODE DONE:" appear as "UNACODE DONE:" and "Good morning!" appears as "morning!".

## Additional Search
- `grep -ri "first.*char\|chunk.*loss\|missing.*char" .claude/`
- `grep -ri "streaming.*race\|content.*drop" .claude/`

## Findings

### Relevant Files & Why They Matter

#### 1. `src/tunacode/core/agents/main.py:174-213` → **Token streaming entry point**
- **Why it matters:** This is where `PartDeltaEvent` and `TextPartDelta` objects are processed from the LLM
- **Key finding:** Line 186 contains `if event.delta.content_delta and streaming_callback:` which filters out empty content deltas
- **Risk level:** HIGH - This could drop the first token if it's empty or None

#### 2. `src/tunacode/ui/panels.py:184-219` → **UI panel content handling**
- **Why it matters:** This is where content chunks are received and displayed to the user
- **Key finding:** Lines 190-203 contain aggressive filtering with early returns that can drop content
- **Risk level:** HIGH - Early return at line 203 causes complete content loss for matching chunks

#### 3. `src/tunacode/core/agents/agent_components/node_processor.py:210-220` → **Fallback streaming**
- **Why it matters:** Provides streaming when pydantic-ai streaming API is unavailable
- **Key finding:** Recent fixes preserve whitespace but JSON thought filtering could still affect content
- **Risk level:** LOW - Intentional filtering, well-tested

#### 4. `src/tunacode/cli/repl.py:333` → **REPL streaming callback setup**
- **Why it matters:** Connects the agent's streaming output to the UI panel
- **Key finding:** Simple lambda callback, minimal risk
- **Risk level:** LOW - Clean implementation

### Key Patterns / Solutions Found

#### 1. **Empty Content Delta Filtering Pattern** (HIGH RISK)
- **Location:** `src/tunacode/core/agents/main.py:186`
- **Pattern:** `if event.delta.content_delta and streaming_callback:`
- **Issue:** LLM providers might send empty initial chunks that get filtered
- **Solution needed:** Allow empty/None content through or handle them specially

#### 2. **Early Return Content Filtering Pattern** (HIGH RISK)
- **Location:** `src/tunacode/ui/panels.py:190-203`
- **Pattern:** Aggressive filtering with `return` statements that drop entire chunks
- **Issue:** First content chunk might match filter patterns and be completely lost
- **Solution needed:** More precise filtering or first-chunk preservation logic

#### 3. **Race Condition Pattern** (MEDIUM RISK)
- **Location:** `src/tunacode/ui/panels.py:151-169` and `184-219`
- **Pattern:** Shared state modification between `update()` and `_animate_dots()` without synchronization
- **Issue:** Concurrent updates can cause state inconsistency and missed content
- **Solution needed:** State synchronization or atomic operations

#### 4. **Thinking... Transition Pattern** (MEDIUM RISK)
- **Location:** `src/tunacode/ui/panels.py:113-132`
- **Pattern:** Transition from "Thinking..." to content display based on `self.content` emptiness
- **Issue:** Race condition between dots animation and first content arrival
- **Solution needed:** Disable dots immediately on first content or use transition guard

### Knowledge Gaps

1. **LLM Provider Behavior:** Need to understand what the first few delta events look like from different providers
2. **Timing Characteristics:** Need to measure the exact timing between stream start and first content arrival
3. **Filter Pattern Matching:** Need to verify if legitimate user content ever matches the filter patterns
4. **Concurrency Impact:** Need to understand the frequency and impact of concurrent update scenarios

### References

#### Complete Data Flow Path
```
1. LLM → PartDeltaEvent → main.py:186 (filter check)
2. main.py:187 → streaming_callback → panels.py:184 (update method)
3. panels.py:190-203 (content filtering) → panels.py:212 (concatenation)
4. panels.py:219 → live.update() → _create_panel() → User display
```

#### Recent Changes Identified
- **Fixed:** Unsafe whitespace stripping in fallback streaming (node_processor.py:215-216)
- **Present:** Empty content delta filtering remains potential issue
- **Present:** Aggressive system prompt filtering in UI panel

#### Code Locations for Investigation
- **High Priority:** `src/tunacode/core/agents/main.py:186`
- **High Priority:** `src/tunacode/ui/panels.py:190-203`
- **Medium Priority:** `src/tunacode/ui/panels.py:151-169`
- **Low Priority:** `src/tunacode/core/agents/agent_components/node_processor.py:217`

## Root Cause Analysis

Based on the evidence, the most likely cause of first-character loss is a combination of:

1. **Empty content delta filtering** at `main.py:186` dropping the first token
2. **Aggressive content filtering** at `panels.py:190-203` causing early returns
3. **Race conditions** between dots animation and first content display

The consistent pattern of losing only the first visible character suggests the issue occurs during the initial transition from "Thinking..." to actual content display, likely in the first 1-2 chunks of the streaming process.
