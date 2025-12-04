# Research – Simple --setup Command Implementation

**Date:** 2025-12-04
**Owner:** Claude Agent
**Phase:** Research

## Goal

Research how to implement a simple `--setup` CLI flow that:
1. Presents a modal to select OpenAI-compatible provider URLs (OpenRouter, Chutes, OpenAI, etc.)
2. Fetches models from https://models.dev/api.json for provider/model data
3. Saves configuration with minimal friction

## Findings

### 1. External API: models.dev

**URL:** `https://models.dev/api.json`

**Structure:**
```
{
  "provider_id": {
    "id": "provider_id",
    "name": "Human Readable Name",
    "api": "https://api.example.com/v1",    // Base URL
    "env": ["API_KEY_ENV_VAR"],              // Required env vars
    "doc": "https://docs.example.com",       // Documentation link
    "models": {
      "model_id": {
        "id": "model_id",
        "name": "Model Name",
        "cost": {
          "input": 0.15,     // per 1M tokens
          "output": 0.60,
          "cache_read": 0.075,
          "cache_write": 0.15
        },
        "limit": {
          "context": 128000,
          "output": 8192
        },
        "modalities": ["text", "image"],
        "reasoning": true,
        "tool_call": true
      }
    }
  }
}
```

**Key Providers Available:**
- OpenAI: `https://api.openai.com/v1`
- OpenRouter: `https://openrouter.ai/api/v1`
- Groq: Standard OpenAI-compatible
- Mistral: `https://api.mistral.ai`
- Alibaba: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- xAI (Grok): via SDK
- Cerebras: `https://api.cerebras.ai/v1`

### 2. CLI Architecture

**File:** `src/tunacode/ui/main.py`

**Framework:** Typer (built on Click)

**Current Flags:**
| Flag | Type | Status | Purpose |
|------|------|--------|---------|
| `--version` / `-v` | bool | Active | Show version |
| `--baseurl` | str | Unused (ARG001) | API base URL |
| `--model` | str | Active | Default model |
| `--key` | str | Unused (ARG001) | API key |
| `--context` | int | Unused (ARG001) | Context window |

**Entry Point Pattern (line 40-50):**
```python
@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="..."),
    # Add --setup here
    setup: bool = typer.Option(False, "--setup", help="Run setup wizard"),
):
```

**Startup Flow:**
1. `main()` → `async_main()`
2. Version check (early return)
3. StateManager initialization (loads config)
4. `run_textual_repl(state_manager)`

### 3. Configuration System

**Config File:** `~/.config/tunacode.json`

**Current Structure:**
```json
{
  "default_model": "openrouter:openai/gpt-4.1",
  "env": {
    "ANTHROPIC_API_KEY": "",
    "OPENAI_API_KEY": "",
    "OPENROUTER_API_KEY": ""
  },
  "settings": {
    "max_retries": 10,
    "max_iterations": 40,
    "enable_streaming": true
  }
}
```

**Key Files:**
| File | Purpose |
|------|---------|
| `src/tunacode/configuration/defaults.py:11-38` | Default config values |
| `src/tunacode/configuration/settings.py:14-17` | Path configuration |
| `src/tunacode/utils/config/user_configuration.py:32-58` | Load/save logic |
| `src/tunacode/core/state.py:107-133` | Config merging |

**Provider Config:** `src/tunacode/core/agents/agent_components/agent_config.py:234-250`
```python
PROVIDER_CONFIG = {
    "anthropic": {"api_key_name": "ANTHROPIC_API_KEY", "base_url": None},
    "openai": {"api_key_name": "OPENAI_API_KEY", "base_url": None},
    "openrouter": {
        "api_key_name": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
    },
    "cerebras": {
        "api_key_name": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1",
    },
}
```

### 4. TUI Components

**Framework:** Textual + Rich + textual-autocomplete

**Existing Setup Wizard:** `src/tunacode/ui/screens/setup.py`
- Uses `Screen[None]` (not modal)
- Has hardcoded 4 providers only
- Uses `Select` widget for provider dropdown
- **Not currently triggered** in startup flow

**Modal Pattern (from confirmation.py):**
```python
class MyModal(ModalScreen[None]):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Title"),
            Select([("Option", "value")], id="select"),
            Button("Save", variant="success"),
            id="modal-body",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.post_message(ResultMessage(data=...))
        self.app.pop_screen()
```

**Available Widgets:**
- `Select` - Dropdown (perfect for provider/model selection)
- `Input` - Text input (for API key)
- `Button` - Actions
- `Label` / `Static` - Text display
- `Vertical` / `Horizontal` - Layout containers

**CSS for Modals:** `src/tunacode/ui/app.tcss:181-214`
```css
ModalScreen {
    align: center middle;
}
#modal-body {
    width: 60;
    height: auto;
    border: solid $primary;
    background: $surface;
    padding: 1 2;
}
```

## Key Patterns / Solutions Found

### Pattern 1: Simple Setup Flow (Recommended)

```
tunacode --setup
    │
    ▼
┌─────────────────────────────────┐
│  Select Provider                │
│  ┌───────────────────────────┐  │
│  │ OpenRouter (recommended) ▼│  │
│  │ OpenAI                    │  │
│  │ Chutes                    │  │
│  │ Groq                      │  │
│  │ ...from models.dev        │  │
│  └───────────────────────────┘  │
│                                 │
│  [Next]                         │
└─────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────┐
│  Select Model                   │
│  ┌───────────────────────────┐  │
│  │ gpt-4.1 ($2.00/1M)       ▼│  │
│  │ gpt-4.1-mini ($0.40/1M)   │  │
│  │ ...filtered by provider   │  │
│  └───────────────────────────┘  │
│                                 │
│  API Key: [________________]    │
│                                 │
│  [Save & Start]                 │
└─────────────────────────────────┘
    │
    ▼
Config saved → Launch REPL
```

### Pattern 2: Fetch models.dev at Runtime

```python
import httpx

async def fetch_providers() -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://models.dev/api.json")
        return resp.json()

def get_provider_choices(data: dict) -> list[tuple[str, str]]:
    """Return (display_name, provider_id) for Select widget."""
    return [
        (f"{p['name']} - {p['api']}", pid)
        for pid, p in data.items()
        if p.get('api')  # Only providers with base URLs
    ]
```

### Pattern 3: Config Save Simplification

For the simplest config, we only need:
```json
{
  "default_model": "openrouter:openai/gpt-4.1",
  "env": {
    "OPENROUTER_API_KEY": "sk-xxx"
  },
  "provider_base_url": "https://openrouter.ai/api/v1"
}
```

**Note:** Current `PROVIDER_CONFIG` hardcodes base URLs. For dynamic providers from models.dev, we need to:
1. Store selected provider's base URL in config
2. Update `agent_config.py` to read `provider_base_url` from config

## Knowledge Gaps

1. **Chutes provider** - Not found in models.dev API. Need to manually add or find correct endpoint.

2. **Dynamic provider support** - Current `PROVIDER_CONFIG` is hardcoded. Need to modify `agent_config.py:266-285` to support custom base URLs from config.

3. **API key naming** - Each provider in models.dev uses different env var names. Need mapping or allow user to specify.

4. **Offline fallback** - What if models.dev is unreachable? Need hardcoded fallback list.

## Implementation Recommendation

### Minimal Changes Required:

1. **Add `--setup` flag** in `src/tunacode/ui/main.py:40-50`

2. **Create simple setup modal** in `src/tunacode/ui/screens/simple_setup.py`:
   - Step 1: Select provider (with base URL)
   - Step 2: Select model + enter API key
   - Save and launch

3. **Update config structure** to support custom base URLs:
   ```python
   # In defaults.py
   "provider": {
       "base_url": "https://openrouter.ai/api/v1",
       "api_key_env": "OPENROUTER_API_KEY"
   }
   ```

4. **Modify agent_config.py** to read base URL from config instead of hardcoded `PROVIDER_CONFIG`

### Popular Provider Quick-List (hardcoded fallback):

| Provider | Base URL | Env Var |
|----------|----------|---------|
| OpenRouter | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |
| OpenAI | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| Groq | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` |
| Cerebras | `https://api.cerebras.ai/v1` | `CEREBRAS_API_KEY` |
| Together | `https://api.together.xyz/v1` | `TOGETHER_API_KEY` |
| Mistral | `https://api.mistral.ai/v1` | `MISTRAL_API_KEY` |

## References

### Codebase Files
- `src/tunacode/ui/main.py` - CLI entry point
- `src/tunacode/ui/screens/setup.py` - Existing setup wizard (partial)
- `src/tunacode/ui/screens/confirmation.py` - Modal pattern example
- `src/tunacode/configuration/defaults.py` - Default config
- `src/tunacode/core/agents/agent_components/agent_config.py:234-285` - Provider handling
- `src/tunacode/utils/config/user_configuration.py` - Config save/load

### External
- https://models.dev/api.json - Provider/model data source
- Textual docs: https://textual.textualize.io/
