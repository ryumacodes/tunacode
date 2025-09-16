from pathlib import Path
from typing import NamedTuple, override

from kosong.base.chat_provider import ChatProvider
from kosong.base.tool import ParametersType
from kosong.context.linear import MemoryLinearStorage
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType, Toolset

from kimi_cli.agent import (
    BuiltinSystemPromptArgs,
    load_agent_by_name,
    load_system_prompt,
    load_tools,
)
from kimi_cli.event import EventQueue, RunEnd, StepCancelled
from kimi_cli.soul import Soul


class Subagent(NamedTuple):
    system_prompt: str
    toolset: Toolset


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
        self._subagents: dict[str, Subagent] = {}

        # load all subagents
        for subagent_name, agent_name in {
            "explorer": "explorer",
            "coder": "koder-sub",
        }.items():
            agent = load_agent_by_name(agent_name)
            assert agent is not None
            system_prompt = load_system_prompt(agent, builtin_args)
            toolset, bad_tools = load_tools(agent)
            assert not bad_tools
            self._subagents[subagent_name] = Subagent(system_prompt, toolset)

    @override
    async def __call__(self, description: str, subagent_name: str, prompt: str) -> ToolReturnType:
        if subagent_name not in self._subagents:
            return ToolError(f"Subagent not found: {subagent_name}", "Subagent not found")
        subagent = self._subagents[subagent_name]
        context_storage = MemoryLinearStorage()
        soul = Soul(
            name=subagent_name,
            chat_provider=self._chat_provider,
            system_prompt=subagent.system_prompt,
            toolset=subagent.toolset,
            context_storage=context_storage,
        )

        async def _visualize(event_queue: EventQueue):
            while True:
                event = await event_queue.get()
                if isinstance(event, StepCancelled | RunEnd):
                    break

        await soul.run(prompt, _visualize)

        # find the last assistant message
        for message in reversed(context_storage.messages):
            if message.role == "assistant":
                return ToolOk(message.content)
        return ToolError("No response from the subagent", "Invalid response")
