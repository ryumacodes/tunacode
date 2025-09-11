import asyncio
from dataclasses import dataclass

from kosong.base.message import ContentPart, ToolCall, ToolCallPart


class RunBegin:
    pass


class RunEnd:
    pass


@dataclass
class StepBegin:
    n: int


type Event = RunBegin | RunEnd | StepBegin | ContentPart | ToolCall | ToolCallPart
EventQueue = asyncio.Queue[Event]
