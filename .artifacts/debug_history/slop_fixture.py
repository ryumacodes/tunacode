from typing import Any, Protocol, cast


class _ModelDumpableMessage(Protocol):
    def model_dump(self, *, exclude_none: bool = False) -> object:
        del exclude_none
        raise NotImplementedError


def bad(message: object) -> dict[str, object]:
    serialized_message = cast(Any, message).model_dump(exclude_none=True)
    if not isinstance(serialized_message, dict):
        raise TypeError("tinyagent message model_dump(exclude_none=True) must return dict")
    return serialized_message
