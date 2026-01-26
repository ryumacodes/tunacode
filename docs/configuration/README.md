# Configuration

TunaCode reads user settings from `~/.config/tunacode.json`. Use the bundled example to seed a new install or reset to the shipped defaults.

## Use the example
1. Create the config directory and copy the sample:
   ```bash
   mkdir -p ~/.config
   cp docs/configuration/tunacode.json.example ~/.config/tunacode.json
   ```
2. Fill in any API keys you plan to use.
3. Tune timeouts and limits to match your environment.

## Field overview
- `default_model`: provider/model the TUI selects on startup.
- `env`: API keys exported to the agent so tools can call providers.
- `settings`: runtime behavior such as retries, iterations, delays, timeouts, streaming, and theme.
- `settings.ripgrep`: search tuning (timeout, result cap, optional metrics).

See `docs/configuration/tunacode.json.example` for the full JSON structure and defaults.

## Tool output limits

Control how much output tools return. Useful for managing context usage.

| Setting | Default | Description |
|---------|---------|-------------|
| `read_limit` | 2000 | Max lines returned by `read_file` |
| `max_line_length` | 2000 | Truncate lines longer than this |
| `max_command_output` | 5000 | Max chars from `bash` output |
| `max_files_in_dir` | 50 | Max entries from `list_dir` |
| `max_tokens` | null | Cap model response length (null = no limit) |

**Precedence**: explicit setting > standard default

Example - shorter file reads for a messy codebase:
```json
{
  "settings": {
    "read_limit": 500
  }
}
```
