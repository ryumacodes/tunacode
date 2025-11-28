"""Test script for StarCraft TUI."""

import asyncio
from tunacode.ui.starcraft_tui import StarCraftTUI


async def simulate_streaming(app: StarCraftTUI):
    """Simulate streaming content."""
    await asyncio.sleep(0.5)

    app.set_model("gpt-4o-mini")
    app.set_tokens(1000)
    app.set_query("Research the ReAct pattern in AI agents")
    app.set_cycle(1, 10)
    app.log_event("starting")

    await asyncio.sleep(0.5)

    app.set_reasoning_steps(["api_call", "tool", "observe", "done"], "api_call")
    app.log_event("api_call gpt-4o-mini")

    await asyncio.sleep(0.5)

    # Simulate streaming content
    content = """# ReAct Pattern in AI Agents

ReAct is a paradigm that combines reasoning traces with actions, allowing LLM agents to solve complex tasks by interleaving thought and tool use.

## Key Concepts

1. **Reasoning**: The agent thinks about what to do
2. **Acting**: The agent takes an action
3. **Observing**: The agent observes the result
"""

    for char in content:
        app.append_content(char)
        app.set_tokens(app.query_one("#resource-bar").tokens + 1)
        await asyncio.sleep(0.01)

    app.set_reasoning_steps(["api_call", "tool", "observe", "done"], "tool")
    app.set_tool("ddgs_search", "query='ReAct pattern AI'", "running")
    app.log_event("tool ddgs_search")

    await asyncio.sleep(1)

    app.set_tool("ddgs_search", "query='ReAct pattern AI'", "done")
    app.set_reasoning_steps(["api_call", "tool", "observe", "done"], "done")
    app.set_status("complete")
    app.set_cost(0.0041)
    app.log_event("done")


async def main():
    app = StarCraftTUI()

    # Run simulation in background
    asyncio.create_task(simulate_streaming(app))

    # Run the app
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
