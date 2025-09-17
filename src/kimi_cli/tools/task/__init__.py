from pathlib import Path
from typing import override

from kosong.base.chat_provider import ChatProvider
from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

from kimi_cli.agent import Agent, BuiltinSystemPromptArgs, get_agents_dir, load_agent
from kimi_cli.context import Context
from kimi_cli.event import EventQueue, RunEnd, StepCancelled
from kimi_cli.soul import Soul


class Task(CallableTool):
    name: str = "task"
    description: str = (Path(__file__).parent / "description.md").read_text()
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
                "description": "The task for the subagent to perform",
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

        # find the last assistant message
        for message in reversed(context.history):
            if message.role == "assistant":
                return ToolOk(message.content)
        return ToolError("No response from the subagent", "Invalid response")
