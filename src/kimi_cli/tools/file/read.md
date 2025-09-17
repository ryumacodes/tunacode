Read content from a file.

**Guidelines:**
- The file path must be absolute.
- When the file is too large (e.g. > 100KB), use `line_offset` and `n_lines` to read a specific range of lines.
