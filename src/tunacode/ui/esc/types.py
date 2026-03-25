"""Protocols for ESC handler dependencies."""

from __future__ import annotations

from typing import Protocol, TypeAlias


class Cancellable(Protocol):
    """Protocol for request handles that can be cancelled."""

    def cancel(self) -> None: ...


RequestTask: TypeAlias = Cancellable


class ShellRunnerProtocol(Protocol):
    """Protocol for shell cancellation dependencies."""

    def is_running(self) -> bool: ...

    def cancel(self) -> None: ...
