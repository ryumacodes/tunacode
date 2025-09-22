import asyncio
from typing import NamedTuple

from kosong.base.message import ContentPart, ToolCall, ToolCallPart
from kosong.tooling import ToolResult


class RunBegin:
    pass


class RunEnd:
    pass


class StepBegin(NamedTuple):
    n: int


class StepInterrupted:
    pass


class ContextUsageUpdate(NamedTuple):
    usage_percentage: float


type ControlFlowEvent = RunBegin | RunEnd | StepBegin | StepInterrupted | ContextUsageUpdate
type Event = ControlFlowEvent | ContentPart | ToolCall | ToolCallPart | ToolResult
EventQueue = asyncio.Queue[Event]
