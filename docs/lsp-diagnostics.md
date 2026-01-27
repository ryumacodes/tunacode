# LSP Diagnostics

TunaCode provides automatic LSP diagnostics feedback when files are written or updated.

## How It Works

When `write_file` or `update_file` tools are called:
1. File operation completes
2. Language server spawns (ruff, tsserver, gopls, etc.)
3. Diagnostics fetched for the file
4. Results appended to tool output

## Configuration

Enable/disable in `~/.tunacode/config.yaml`:

```yaml
settings:
  lsp:
    enabled: true
    timeout: 5.0
```

## Requirements

Install language servers for your languages:

- **Python**: `pip install ruff`
- **TypeScript/JavaScript**: `npm install -g typescript-language-server`
- **Go**: `go install golang.org/x/tools/gopls@latest`
- **Rust**: `rustup component add rust-analyzer`

## Output Format

```
<file_diagnostics>
ACTION REQUIRED: 2 error(s) found - fix before continuing
Error (line 15): undefined name 'x'
Error (line 23): missing return statement
</file_diagnostics>
```

The agent receives this as contextual feedback and decides how to respond.

## Architecture

LSP lives in `tools/lsp/` as a tool-layer concern:
- `tools.lsp.get_diagnostics()` - fetch diagnostics
- `tools.lsp.format_diagnostics()` - format for output
- `tools.write_file` and `tools.update_file` call these automatically
