Read content from a file.

**Tips:**
- Make sure you follow the description of each tool parameter.
- For files you are sure is large or that you only need part of the content, read it with `line_offset` and `n_lines` parameters. When you are not sure, try to read the entire file first. A system notice will be returned if the file is too large to read at once.
- Any lines longer than ${MAX_LINE_LENGTH} characters will be truncated, ending with "...".
- A `<system>` tag will be given before the read file content.
- Content will be returned with a line number before each line like `cat -n` format.
- This tool is a typical tool that is encouraged to be used in parallel. Always read multiple files in one response when possible.
- Can only read text files. To list directories, use Glob tool or `ls` command via the Bash tool. To read other file types, use appropriate tools via Bash.
- If the file doesn't exist or path is invalid, an error will be returned.
- If you want to search for a certain content/pattern, prefer Grep tool over ReadFile.
