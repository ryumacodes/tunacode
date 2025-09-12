import asyncio
from typing import NamedTuple

from kosong.base.message import ContentPart, ToolCall, ToolCallPart


class RunBegin:
    pass


class RunEnd:
    pass


class StepBegin(NamedTuple):
    n: int


type ControlFlowEvent = RunBegin | RunEnd | StepBegin
type Event = ControlFlowEvent | ContentPart | ToolCall | ToolCallPart
EventQueue = asyncio.Queue[Event]
