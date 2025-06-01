"""Thin wrapper around OpenAI chat completion used for planning."""
from typing import Any, List, Type

# Placeholder stub for the actual OpenAI integration. This allows unit tests to
# run without network access. In production this should call the real API.
async def chat_completion(*, system: str, user: str, schema: Type[Any], array_response: bool) -> List[Any]:
    raise RuntimeError("OpenAI integration not available in this environment")
