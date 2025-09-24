import asyncio
from typing import override

from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolOk, ToolReturnType


class Plus(CallableTool):
    name: str = "plus"
    description: str = "Add two numbers"
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
        "required": ["a", "b"],
    }

    @override
    async def __call__(self, a: float, b: float) -> ToolReturnType:
        return ToolOk(output=str(a + b))


class Compare(CallableTool):
    name: str = "compare"
    description: str = "Compare two numbers"
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
        },
    }

    @override
    async def __call__(self, a: float, b: float) -> ToolReturnType:
        if a > b:
            return ToolOk(output="greater")
        elif a < b:
            return ToolOk(output="less")
        else:
            return ToolOk(output="equal")


class Panic(CallableTool):
    name: str = "panic"
    description: str = "Raise an exception to cause the tool call to fail."
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
        },
    }

    @override
    async def __call__(self, message: str) -> ToolReturnType:
        await asyncio.sleep(2)
        raise Exception(f"panicked with a message with {len(message)} characters")
