import asyncio
from typing import override

from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool


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
    async def __call__(self, a: float, b: float) -> float:
        return a + b


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
    async def __call__(self, a: float, b: float) -> str:
        if a > b:
            return "greater"
        elif a < b:
            return "less"
        else:
            return "equal"


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
    async def __call__(self, message: str) -> str:
        await asyncio.sleep(2)
        raise Exception(f"panicked with a message with {len(message)} characters")
