Read content from a file.

**Usage:**
- The file path must be absolute.
- By default reads up to 2000 lines starting from line 1 (2000 is the max lines allowed in a single call).
- For large files, use `line_offset` and `n_lines` to read specific sections. However, it is recommended to read the whole file in the first try.
- Any lines longer than 2000 characters will be truncated, ending with "...".
- Content will be returned after a <system-message> tag.
- Content will be returned with a line number before each line like `cat -n` format.
- You have the ability to spawn multiple tool calls in one response. It is highly encouraged to read multiple files with parallel tool calls.
- Can only read files, not directories. To list directories, use `ls` command via the `bash` tool.
- If the file doesn't exist or path is invalid, an error will be returned.
