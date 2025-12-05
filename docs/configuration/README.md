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
- `settings.ripgrep`: search tuning (timeout, buffer size, result cap, optional metrics and debug logging).

See `docs/configuration/tunacode.json.example` for the full JSON structure and defaults.
