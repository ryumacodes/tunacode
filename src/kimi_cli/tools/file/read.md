Read content from a file.

**Tips:**
- Make sure you follow the description of the description of each tool parameter.
- For files you are sure is large, read it in chunks, or use Grep tool to search for specific content.
- Any lines longer than 2000 characters will be truncated, ending with "...".
- A `<system>` tag will be given before the read file content.
- Content will be returned with a line number before each line like `cat -n` format.
- This tool is a typical tool that is encouraged to be used in parallel. Always read multiple files in one response when possible.
- Can only read files, not directories. To list directories, use Glob tool or `ls` command via the Bash tool.
- If the file doesn't exist or path is invalid, an error will be returned.
