---
type: deep-search
query: "simple eval for LLM prompts - tunacode system prompt evaluation"
date: 2026-01-09
sources: [web-search, gemini, agent-knowledge]
---

# Deep Search: Simple Prompt Evaluation for Tunacode

## Query Analysis

- **Perspective 1**: Lightweight eval frameworks for code agents
- **Perspective 2**: Measuring prompt quality without complex infrastructure
- **Perspective 3**: Practical approaches teams use in 2025

## Findings by Source

### Web Search Results

**Top frameworks identified:**

1. **Promptfoo** - CLI-first, YAML-based test cases, LLM-as-judge support
2. **DeepEval** - Pytest-like interface for LLM testing
3. **OpenAI Evals** - JSON/YAML config, no code needed for basic evals
4. **RAGAS** - Specialized for RAG evaluation

### Gemini Search Results (Real-time Google grounding)

**Key insights for code agents:**

- Promptfoo is the most recommended for CLI tools
- DeepEval fits naturally into Python projects
- Aider uses "polyglot benchmark" approach: run agent on small coding tasks, check syntax/exit codes
- Trace-based evaluation gaining popularity (evaluate steps, not just final output)

**Practical patterns teams use:**

- **80/20 Rule**: 80% automated (syntax, schema, forbidden words), 20% human spot-check
- **CI Integration**: Treat prompts like code, run eval suite on prompt changes
- **Synthetic data**: Use LLM to generate diverse test inputs

## Synthesis

### Consensus (All sources agree)

1. **Promptfoo is the go-to for simple evals** - YAML config, CLI-first, perfect for tunacode
2. **LLM-as-Judge works well** for subjective quality metrics
3. **Deterministic assertions first** - syntax checks, format validation, forbidden patterns
4. **Golden test sets** of 10-50 examples is sufficient to start
5. **Treat prompts like code** - version control, regression testing in CI

### Key Approaches for Tunacode

#### Option A: Minimal (Code-First)

```python
# tests/test_prompt_eval.py
def test_prompt_no_forbidden_patterns():
    """System prompt should not contain anti-patterns."""
    prompt = load_system_prompt()
    assert "you are helpful" not in prompt.lower()  # generic
    assert "step by step" not in prompt.lower()  # filler

def test_prompt_has_required_sections():
    """System prompt should have key sections."""
    prompt = load_system_prompt()
    required = ["Tool usage", "Code style", "Error handling"]
    for section in required:
        assert section.lower() in prompt.lower()

def test_prompt_length_reasonable():
    """Prompt should not exceed token budget."""
    prompt = load_system_prompt()
    # Rough estimate: 4 chars per token
    assert len(prompt) < 50000  # ~12k tokens max
```

#### Option B: Promptfoo (YAML-Driven)

```yaml
# promptfoo.yaml
prompts:
  - file://CLAUDE.md

providers:
  - openai:gpt-4o-mini  # cheap judge

tests:
  - vars:
      task: "Fix a type error in Python"
    assert:
      - type: llm-rubric
        value: "Response should suggest using type hints or fixing the type mismatch"
      - type: not-contains
        value: "I cannot"

  - vars:
      task: "Refactor this function to be more readable"
    assert:
      - type: llm-rubric
        value: "Response should reference guard clauses, early returns, or code clarity"
```

#### Option C: Hybrid (Recommended for Tunacode)

1. **Static checks** (pytest): Length, required sections, forbidden patterns
2. **Behavioral tests** (promptfoo): Run prompt against test scenarios
3. **LLM-as-Judge** (optional): For subjective quality scores

### Minimal Implementation Plan

```
tests/
  test_prompt_static.py      # Static prompt checks
  prompts/
    test_cases.yaml          # Golden test scenarios
    promptfoo.yaml           # Promptfoo config (optional)
```

**Static checks to implement:**

| Check | Purpose |
|-------|---------|
| Length < 15k tokens | Stay within context budgets |
| Has required sections | Ensure completeness |
| No forbidden patterns | Avoid generic/filler content |
| Consistent formatting | XML tags closed, markdown valid |
| No conflicting instructions | Detect contradictions |

**Behavioral checks:**

| Scenario | Expected Behavior |
|----------|-------------------|
| "Fix type error" | References type hints, not generic advice |
| "Add feature" | Uses TodoWrite, plans before coding |
| "Read file" | Uses Read tool, not Bash cat |
| "Security question" | Refuses if malicious, helps if authorized |

## Recommended Next Steps

1. **Start with static checks** - Add `tests/test_prompt_static.py`
2. **Create 10 golden test cases** - Representative user tasks
3. **Add promptfoo later** if static checks aren't enough
4. **Run in CI** - Block prompt changes that break tests

## Sources

- [Promptfoo GitHub](https://github.com/promptfoo/promptfoo)
- [DeepEval](https://deepeval.com/)
- [OpenAI Evals](https://github.com/openai/evals)
- [OpenAI Evaluation Best Practices](https://platform.openai.com/docs/guides/evaluation-best-practices)
- [LLM Eval Landscape](https://research.aimultiple.com/llm-eval-tools/)
- [How to Build LLM Eval from Scratch](https://www.confident-ai.com/blog/how-to-build-an-llm-evaluation-framework-from-scratch)
