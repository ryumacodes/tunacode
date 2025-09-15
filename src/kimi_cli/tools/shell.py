import asyncio
from typing import override

from kosong.base.tool import ParametersType
from kosong.tooling import CallableTool, ToolError, ToolOk, ToolReturnType

_DESCRIPTION = """
Execute a shell command. Use this tool to explore the filesystem, edit files, \
run scripts, get system information, etc.

**Output:**
The stdout and stderr will be streamed to somewhere the user can see, and also returned \
as a string. The output may be truncated or compressed if it is too long. The exit code \
will be appended to the end of the returned string.

**Guidelines for safety and security:**
- Each shell tool call will be executed in a fresh shell environment. The shell variables, \
  current working directory changes, and the shell history is not preserved between calls.
- The tool call will return after the command is finished. You shall not use this tool \
  to execute an interactive command or a command that may run forever. For possibly long- \
  running commands, you shall set `timeout` argument to a reasonable value.
- Avoid using `..` to access files or directories outside of the working directory.
- Avoid modifying files outside of the working directory unless explicitly instructed to do so.
- Never run commands that require superuser privileges unless explicitly instructed to do so.

**Guidelines for efficiency:**
- For multiple related commands, use `&&` to chain them in a single call, e.g. `cd /path && ls -la`
- Use `;` to run commands sequentially regardless of success/failure
- Use `||` for conditional execution (run second command only if first fails)
- Use pipe operations (`|`) and redirections (`>`, `>>`) to chain input and output between commands
- Always quote file paths containing spaces with double quotes (e.g., cd "/path with spaces/")
- Use `if`, `case`, `for`, `while` control flows to execute complex logic in a single call.
- Verify directory structure before create/edit/delete files or directories to reduce the risk of \
  failure.

**Commands available:**
- Shell environment: cd, pwd, export, unset, env
- File system operations: ls, find, grep, cat, mkdir, rm, cp, mv, touch, chmod, chown
- File viewing/editing: cat (can use >> to append), echo, head, tail, diff, patch
- Text processing: awk, sed, sort, uniq, wc
- System information/operations: ps, kill, top, df, free, uname, whoami, id, date
- Package management: pip, uv, npm, yarn, bun, cargo
- Network operations: curl, wget, ping, telnet, ssh
- Archive operations: tar, zip, unzip
- Other: Other commands available in the shell environment. Check the existence of a command \
  by running `which <command>` before using it.
""".strip()


class Shell(CallableTool):
    name: str = "shell"
    description: str = _DESCRIPTION
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
