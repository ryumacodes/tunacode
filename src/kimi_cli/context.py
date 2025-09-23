import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

from kosong.base.message import Message

from kimi_cli.logging import logger


class Context:
    def __init__(self, file_backend: Path | None = None):
        self._file_backend = file_backend
        self._history: list[Message] = []
        self._token_count: int = 0

    async def restore(self):
        logger.debug("Restoring context from file: {file_backend}", file_backend=self._file_backend)
        if self._history:
            logger.error("The context storage is already modified")
            raise RuntimeError("The context storage is already modified")
        if not self._file_backend or not self._file_backend.exists():
            logger.debug("No context file found, skipping restoration")
            return

        def _restore():
            assert self._file_backend is not None
            with open(self._file_backend, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    line_json = json.loads(line)
                    if "token_count" in line_json:
                        self._token_count = line_json["token_count"]
                        continue
                    message = Message.model_validate(line_json)
                    self._history.append(message)

        await asyncio.to_thread(_restore)

    @property
    def history(self) -> Sequence[Message]:
        return self._history

    @property
    def token_count(self) -> int:
        return self._token_count

    async def checkpoint(self):
        raise NotImplementedError("Checkpoint is not implemented")

    async def pop_checkpoint(self):
        raise NotImplementedError("Pop checkpoint is not implemented")

    async def append_message(self, message: Message | Sequence[Message]):
        logger.debug("Appending message(s) to context: {message}", message=message)
        messages = message if isinstance(message, Sequence) else [message]
        self._history.extend(messages)

        def _append_to_file():
            assert self._file_backend is not None
            with open(self._file_backend, "a", encoding="utf-8") as f:
                for message in messages:
                    f.write(message.model_dump_json(exclude_none=True) + "\n")

        if self._file_backend:
            await asyncio.to_thread(_append_to_file)

    async def update_token_count(self, token_count: int):
        logger.debug("Updating token count in context: {token_count}", token_count=token_count)
        self._token_count = token_count

        def _append_token_count_to_file():
            assert self._file_backend is not None
            with open(self._file_backend, "a", encoding="utf-8") as f:
                f.write(json.dumps({"role": "_usage", "token_count": token_count}) + "\n")

        if self._file_backend:
            await asyncio.to_thread(_append_token_count_to_file)
