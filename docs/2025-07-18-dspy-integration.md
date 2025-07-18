# DSPy Integration in TunaCode

## Overview

TunaCode now includes DSPy (Demonstrate-Search-Predict) optimization for enhanced tool selection and task planning, providing up to 3x performance improvements through intelligent parallel execution of read-only tools.

## Features

### 1. Optimized Tool Selection
- Automatically batches 3-4 read-only tools for parallel execution
- Uses Chain of Thought reasoning for tool selection
- Learned patterns from DSPy optimization ensure optimal performance

### 2. Enhanced Task Planning
- Automatically detects complex tasks that need breakdown
- Creates todo lists for multi-step implementations
- Identifies parallelization opportunities

### 3. Smart Batching
- Groups `grep`, `list_dir`, `glob`, and `read_file` operations
- Executes write/modify operations sequentially for safety
- Optimal batch size of 3-4 tools based on performance testing

## Configuration

DSPy optimization is enabled by default. To disable it, add to your `~/.config/tunacode.json`:

```json
{
  "settings": {
    "use_dspy_optimization": false
  }
}
```

## API Key Setup

For full DSPy functionality with OpenRouter models, set your API key:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Or add it to your TunaCode config:

```json
{
  "env": {
    "OPENROUTER_API_KEY": "your-api-key-here"
  }
}
```

## Performance Benefits

### Before DSPy
```
- read_file("main.py")     [300ms]
- read_file("config.py")   [300ms]  
- grep("error", "logs/")   [300ms]
Total: 900ms (sequential)
```

### After DSPy
```
Parallel batch:
- read_file("main.py")
- read_file("config.py")
- grep("error", "logs/")
Total: ~350ms (2.6x faster!)
```

## Complex Task Handling

When DSPy detects a complex task (e.g., "implement authentication"), it will:

1. Analyze the request complexity
2. Break it down into subtasks
3. Create a todo list automatically
4. Identify which subtasks can run in parallel

## Technical Details

### DSPy Prompts
- Tool selection prompt: `src/tunacode/prompts/dspy_tool_selection.md`
- Task planning prompt: `src/tunacode/prompts/dspy_task_planning.md`

### Integration Points
- `DSPyIntegration` class in `src/tunacode/core/agents/dspy_integration.py`
- Enhanced system prompt generation in agent creation
- Automatic task breakdown in `process_request()`

### Learned Patterns
1. **3-4 Tool Batching**: Optimal for performance vs cognitive load
2. **Read-Only Parallelization**: Safe to execute concurrently
3. **Sequential Writes**: Maintains data integrity
4. **Search → Read → Modify**: Common debugging pattern

## Troubleshooting

If DSPy optimization isn't working:

1. Check that `use_dspy_optimization` is `true` in settings
2. Verify DSPy is installed: `pip install dspy-ai`
3. For OpenRouter features, ensure `OPENROUTER_API_KEY` is set
4. Check logs for DSPy-related warnings

## Future Enhancements

- Custom DSPy prompt training for project-specific patterns
- Integration with more LLM providers
- Advanced parallelization strategies
- Performance metrics dashboard