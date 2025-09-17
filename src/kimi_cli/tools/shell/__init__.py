import asyncio
from pathlib import Path
from typing import override

from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType


class Shell(CallableTool):
    name: str = "shell"
    description: str = (Path(__file__).parent / "shell.md").read_text()
    parameters: ParametersType = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            },
            "timeout": {
                "type": "number",
                "description": "The timeout in seconds for the command to execute. \
                    If the command takes longer than this, it will be killed.",
                "default": 60,
            },
        },
        "required": ["command"],
    }

    @override
    async def __call__(self, command: str, timeout: int = 60) -> ToolReturnType:
        output = []

        def stdout_cb(line: bytes):
            line_str = line.decode()
            output.append(line_str)

        def stderr_cb(line: bytes):
            line_str = line.decode()
            output.append(line_str)

        try:
            exitcode = await _stream_subprocess(command, stdout_cb, stderr_cb, timeout)
            output_str = "".join(output) + f"\n(Exit code: {exitcode})"
            # TODO: truncate/compress the output if it is too long
            if exitcode == 0:
                return ToolOk(output_str)
            return ToolError(output_str, f"Failed with exit code: {exitcode}")
        except TimeoutError:
            output.append(f"\n(Killed by timeout ({timeout}s))")
            output_str = "".join(output)
            return ToolError(output_str, f"Killed by timeout ({timeout}s)")


async def _stream_subprocess(command: str, stdout_cb, stderr_cb, timeout: int) -> int:
    async def _read_stream(stream, cb):
        while True:
            line = await stream.readline()
            if line:
                cb(line)
            else:
                break

    # FIXME: if the event loop is cancelled, an exception may be raised when the process finishes
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    try:
        await asyncio.wait_for(
            asyncio.gather(
                _read_stream(process.stdout, stdout_cb),
                _read_stream(process.stderr, stderr_cb),
            ),
            timeout,
        )
        return await process.wait()
    except TimeoutError:
        process.kill()
        raise
