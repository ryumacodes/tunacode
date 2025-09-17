from pathlib import Path
from typing import override

from kosong.base.chat_provider import ChatProvider
from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

from kimi_cli.agent import Agent, BuiltinSystemPromptArgs, get_agents_dir, load_agent
from kimi_cli.context import Context
from kimi_cli.event import EventQueue, RunEnd, StepCancelled
from kimi_cli.soul import Soul
from kimi_cli.utils.message import message_extract_text

# Maximum continuation attempts for task summary
_MAX_CONTINUE = 1


_CONTINUE_PROMPT = """
Your previous response was too brief. Please provide a more comprehensive summary that includes:
1. Specific technical details and implementations
2. Complete code examples if relevant
3. Detailed findings and analysis
4. All important information that should be aware of by the caller

Please expand with comprehensive details.
""".strip()


class Task(CallableTool):
    name: str = "task"
    description: str = (Path(__file__).parent / "task.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "A short (3-5 word) description of the task",
            },
            "subagent_name": {
                "type": "string",
                "description": "The name of the specialized subagent to use for this task",
            },
            "prompt": {
                "type": "string",
                "description": (
                    "The task for the subagent to perform. "
                    "This prompt should be accurate and specific to the task. "
                    "Neccesary background should be provided in a concise manner."
                ),
            },
        },
        "required": ["description", "subagent_name", "prompt"],
    }

    def __init__(
        self, chat_provider: ChatProvider, builtin_args: BuiltinSystemPromptArgs, **kwargs
    ):
        super().__init__(**kwargs)
        self._chat_provider = chat_provider
        self._subagents: dict[str, Agent] = {}

        # load all subagents
        for subagent_name, agent_file in {
            "explorer": get_agents_dir() / "explorer" / "agent.yaml",
            "coder": get_agents_dir() / "koder" / "sub.yaml",
        }.items():
            self._subagents[subagent_name] = load_agent(agent_file, builtin_args, chat_provider)

    @override
    async def __call__(self, description: str, subagent_name: str, prompt: str) -> ToolReturnType:
        if subagent_name not in self._subagents:
            return ToolError(f"Subagent not found: {subagent_name}", "Subagent not found")
        agent = self._subagents[subagent_name]
        try:
            result = await self._run_subagent(agent, prompt)
            return result
        except Exception as e:
            return ToolError(f"Failed to run subagent: {e}", "Failed to run subagent")

    async def _run_subagent(self, agent: Agent, prompt: str) -> ToolReturnType:
        """Run subagent with optional continuation for task summary."""
        context = Context()
        soul = Soul(
            agent,
            chat_provider=self._chat_provider,
            context=context,
        )

        async def _visualize(event_queue: EventQueue):
            while True:
                event = await event_queue.get()
                if isinstance(event, StepCancelled | RunEnd):
                    break

        await soul.run(prompt, _visualize)

        _error_msg = (
            "The subagent seemed not to run properly. Maybe you have to do the task yourself."
        )

        # Check if the subagent context is valid
        if len(context.history) == 0 or context.history[-1].role != "assistant":
            return ToolError(_error_msg, "Failed to run subagent")

        final_response = message_extract_text(context.history[-1])

        # Check if response is too brief, if so, run again with continuation prompt
        n_attempts_remaining = _MAX_CONTINUE
        if len(final_response) < 200 and n_attempts_remaining > 0:
            await soul.run(_CONTINUE_PROMPT, _visualize)

            if len(context.history) == 0 or context.history[-1].role != "assistant":
                return ToolError(_error_msg, "Failed to run subagent")
            final_response = message_extract_text(context.history[-1])

        return ToolOk(final_response)
