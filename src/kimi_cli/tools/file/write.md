Write content to a file.

**Guidelines:**
- The file path must be absolute.
- When `mode` is not specified, it defaults to `overwrite`. So write with caution.
- When the content to write is too large (e.g. > 100 lines), use this tool multiple times instead of a single call with a large content. In this case, you should use `append` mode to append to the file after the first write.
