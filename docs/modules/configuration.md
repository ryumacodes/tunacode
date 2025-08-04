<!-- This document covers user configuration (~/.config/tunacode.json), model management, environment variables, and settings -->

# TunaCode Configuration System Documentation

## Overview

TunaCode's configuration system manages application settings, model configurations, and user preferences. It provides a layered approach with defaults, user overrides, and runtime modifications, all persisted in a JSON configuration file.

## Architecture

```
┌─────────────────────────────────────────┐
│          Configuration Layers            │
├─────────────────────────────────────────┤
│  1. Built-in Defaults (defaults.py)     │
│  2. User Config (~/.config/tunacode.json)│
│  3. Environment Variables               │
│  4. Runtime Overrides                   │
└─────────────────────────────────────────┘
```

## Configuration Files

### 1. Application Settings (settings.py)

Core application configuration and constants:

```python
@dataclass(frozen=True)
class PathConfig:
    """Configuration file paths"""
    CONFIG_DIR: Path = Path.home() / ".config" / "tunacode"
    CONFIG_FILE: Path = CONFIG_DIR / "tunacode.json"
    TEMPLATES_DIR: Path = CONFIG_DIR / "templates"
    LOGS_DIR: Path = CONFIG_DIR / "logs"

@dataclass(frozen=True)
class ApplicationSettings:
    """Core application settings"""
    APP_NAME: str = "tunacode"
    VERSION: str = "0.0.51"

    # Tool registry
    INTERNAL_TOOLS: List[str] = field(default_factory=lambda: [
        "read_file",
        "write_file",
        "update_file",
        "run_command",
        "bash",
        "grep",
        "list_dir",
        "glob",
        "todo"
    ])

    # Tool categorization
    READ_ONLY_TOOLS: List[str] = field(default_factory=lambda: [
        "read_file", "grep", "list_dir", "glob"
    ])

    WRITE_TOOLS: List[str] = field(default_factory=lambda: [
        "write_file", "update_file", "todo"
    ])

    EXECUTE_TOOLS: List[str] = field(default_factory=lambda: [
        "run_command", "bash"
    ])

    # Performance settings
    MAX_PARALLEL_TOOLS: int = field(default_factory=lambda:
        int(os.environ.get("TUNACODE_MAX_PARALLEL", str(os.cpu_count() or 4)))
    )

    # Context limits
    DEFAULT_CONTEXT_WINDOW: int = 200000
    DEFAULT_MAX_RESPONSE_TOKENS: int = 4096
```

### 2. Default Configuration (defaults.py)

User-modifiable default settings:

```python
DEFAULT_CONFIG = {
    "default_model": "anthropic:claude-3-5-sonnet-20241022",

    "context_window": 200000,
    "max_response_tokens": 4096,
    "max_iterations": 10,

    "streaming": True,
    "show_thoughts": False,
    "yolo_mode": False,

    "tool_options": {
        "auto_approve_reads": False,
        "require_confirmation": True,
        "show_diffs": True
    },

    "ui_options": {
        "theme": "default",
        "show_costs": True,
        "show_tokens": True,
        "show_spinner": True
    },

    "mcp_servers": {},

    "env": {
        # API keys populated from environment
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
        "PERPLEXITY_API_KEY": os.environ.get("PERPLEXITY_API_KEY"),
        "GROQ_API_KEY": os.environ.get("GROQ_API_KEY"),
        "TOGETHER_API_KEY": os.environ.get("TOGETHER_API_KEY"),
        "FIREWORKS_API_KEY": os.environ.get("FIREWORKS_API_KEY"),
        "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY"),
    }
}
```

### 3. Model Registry (models.py)

Comprehensive model configurations with pricing:

```python
@dataclass
class ModelInfo:
    """Model metadata and pricing"""
    provider: str
    name: str
    display_name: str
    context_window: int
    max_output_tokens: int
    supports_tools: bool
    supports_vision: bool
    input_price_per_million: float  # USD per 1M tokens
    output_price_per_million: float # USD per 1M tokens

    @property
    def model_id(self) -> str:
        """Full model identifier"""
        return f"{self.provider}:{self.name}"

# Model registry with pricing (as of 2024)
MODEL_REGISTRY = {
    # Anthropic Models
    "anthropic:claude-3-5-sonnet-20241022": ModelInfo(
        provider="anthropic",
        name="claude-3-5-sonnet-20241022",
        display_name="Claude 3.5 Sonnet",
        context_window=200000,
        max_output_tokens=8192,
        supports_tools=True,
        supports_vision=True,
        input_price_per_million=3.00,
        output_price_per_million=15.00
    ),

    "anthropic:claude-3-opus-20240229": ModelInfo(
        provider="anthropic",
        name="claude-3-opus-20240229",
        display_name="Claude 3 Opus",
        context_window=200000,
        max_output_tokens=4096,
        supports_tools=True,
        supports_vision=True,
        input_price_per_million=15.00,
        output_price_per_million=75.00
    ),

    # OpenAI Models
    "openai:gpt-4o": ModelInfo(
        provider="openai",
        name="gpt-4o",
        display_name="GPT-4o",
        context_window=128000,
        max_output_tokens=16384,
        supports_tools=True,
        supports_vision=True,
        input_price_per_million=2.50,
        output_price_per_million=10.00
    ),

    "openai:o1-preview": ModelInfo(
        provider="openai",
        name="o1-preview",
        display_name="O1 Preview",
        context_window=128000,
        max_output_tokens=32768,
        supports_tools=False,  # No tool support yet
        supports_vision=False,
        input_price_per_million=15.00,
        output_price_per_million=60.00
    ),

    # Google Models
    "google:gemini-2.0-flash-exp": ModelInfo(
        provider="google",
        name="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash",
        context_window=1048576,  # 1M context
        max_output_tokens=8192,
        supports_tools=True,
        supports_vision=True,
        input_price_per_million=0.00,  # Free during preview
        output_price_per_million=0.00
    ),

    # ... many more models ...
}

# Provider configurations
PROVIDER_CONFIGS = {
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "requires_api_key": True,
        "base_url": None
    },
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "requires_api_key": True,
        "base_url": None
    },
    "google": {
        "api_key_env": "GOOGLE_API_KEY",
        "requires_api_key": True,
        "base_url": None
    },
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "requires_api_key": True,
        "base_url": "https://openrouter.ai/api/v1"
    },
    # Local providers
    "ollama": {
        "api_key_env": None,
        "requires_api_key": False,
        "base_url": "http://localhost:11434"
    }
}
```

## User Configuration

### Configuration File Location

User configuration is stored at `~/.config/tunacode/tunacode.json`:

```json
{
    "default_model": "anthropic:claude-3-5-sonnet-20241022",
    "context_window": 200000,
    "max_response_tokens": 4096,
    "max_iterations": 10,
    "streaming": true,
    "show_thoughts": false,
    "yolo_mode": false,

    "tool_options": {
        "auto_approve_reads": false,
        "require_confirmation": true,
        "show_diffs": true
    },

    "ui_options": {
        "theme": "default",
        "show_costs": true,
        "show_tokens": true,
        "show_spinner": true
    },

    "mcp_servers": {
        "example-server": {
            "command": "node",
            "args": ["path/to/server.js"],
            "env": {
                "API_KEY": "secret"
            }
        }
    },

    "env": {
        "ANTHROPIC_API_KEY": "sk-...",
        "OPENAI_API_KEY": "sk-..."
    }
}
```

### Configuration Loading (user_configuration.py)

```python
def load_user_config() -> Dict[str, Any]:
    """Load user configuration with defaults"""
    config_path = PathConfig.CONFIG_FILE

    # Start with defaults
    config = DEFAULT_CONFIG.copy()

    # Load user config if exists
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)

            # Deep merge with defaults
            config = deep_merge(config, user_config)

        except Exception as e:
            logger.warning(f"Failed to load config: {e}")

    # Override with environment variables
    config = apply_env_overrides(config)

    return config

def save_user_config(config: Dict[str, Any]) -> None:
    """Save user configuration"""
    config_path = PathConfig.CONFIG_FILE

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Write config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2, sort_keys=True)
```

## Configuration Management

### StateManager Integration

The StateManager maintains runtime configuration:

```python
class StateManager:
    def __init__(self):
        # Load user configuration
        self.state.user_config = load_user_config()

        # Extract common settings
        self.state.default_model = self.state.user_config.get("default_model")
        self.state.context_window = self.state.user_config.get("context_window", 200000)
        self.state.max_response_tokens = self.state.user_config.get("max_response_tokens", 4096)
        self.state.max_iterations = self.state.user_config.get("max_iterations", 10)

        # UI settings
        self.state.is_streaming = self.state.user_config.get("streaming", True)
        self.state.show_thoughts = self.state.user_config.get("show_thoughts", False)
        self.state.yolo_mode = self.state.user_config.get("yolo_mode", False)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update and persist configuration"""
        # Update runtime state
        self.state.user_config.update(updates)

        # Update specific state fields
        if "default_model" in updates:
            self.state.default_model = updates["default_model"]
        if "streaming" in updates:
            self.state.is_streaming = updates["streaming"]
        # ... etc

        # Persist to disk
        save_user_config(self.state.user_config)
```

### Environment Variable Overrides

Environment variables can override configuration:

```python
def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides"""

    # Model override
    if env_model := os.environ.get("TUNACODE_MODEL"):
        config["default_model"] = env_model

    # API key overrides
    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]:
        if env_value := os.environ.get(key):
            config["env"][key] = env_value

    # Feature flags
    if os.environ.get("TUNACODE_YOLO") == "true":
        config["yolo_mode"] = True

    if os.environ.get("TUNACODE_NO_STREAMING") == "true":
        config["streaming"] = False

    # Performance settings
    if max_parallel := os.environ.get("TUNACODE_MAX_PARALLEL"):
        config["max_parallel_tools"] = int(max_parallel)

    return config
```

## MCP Server Configuration

Model Context Protocol servers are configured in the user config:

```python
"mcp_servers": {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        "env": {}
    },

    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_TOKEN": "${GITHUB_TOKEN}"
        }
    },

    "custom-tools": {
        "command": "python",
        "args": ["/path/to/custom_mcp_server.py"],
        "env": {
            "API_KEY": "${CUSTOM_API_KEY}"
        }
    }
}
```

### MCP Manager Integration

```python
class MCPManager:
    async def initialize_from_config(self, config: Dict[str, Any]):
        """Initialize MCP servers from configuration"""
        mcp_config = config.get("mcp_servers", {})

        for server_name, server_config in mcp_config.items():
            try:
                # Resolve environment variables
                resolved_config = self._resolve_env_vars(server_config)

                # Start server
                await self.start_server(server_name, resolved_config)

            except Exception as e:
                logger.error(f"Failed to start MCP server {server_name}: {e}")
```

## API Key Management

### Secure Key Storage

API keys are stored in the configuration file's `env` section:

```python
def validate_api_keys(config: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Validate and return available API keys"""
    api_keys = {}
    env_config = config.get("env", {})

    for provider, key_name in PROVIDER_CONFIGS.items():
        if not key_name["requires_api_key"]:
            api_keys[provider] = "not_required"
            continue

        key_env = key_name["api_key_env"]

        # Check config first, then environment
        api_key = env_config.get(key_env) or os.environ.get(key_env)

        if api_key and api_key.strip():
            # Basic validation
            if provider == "anthropic" and not api_key.startswith("sk-"):
                logger.warning(f"Invalid {provider} API key format")
                api_keys[provider] = None
            else:
                api_keys[provider] = api_key
        else:
            api_keys[provider] = None

    return api_keys
```

### API Key Setup Flow

During initial setup:

```python
class EnvironmentSetup(BaseSetup):
    async def run(self, context: SetupContext) -> SetupResult:
        """Validate environment and API keys"""

        # Check for API keys
        api_keys = validate_api_keys(context.config)

        # Find providers with keys
        available_providers = [
            provider for provider, key in api_keys.items()
            if key and key != "not_required"
        ]

        if not available_providers:
            # Prompt for at least one API key
            provider = await self._prompt_provider_selection()
            api_key = await self._prompt_api_key(provider)

            # Update config
            key_name = PROVIDER_CONFIGS[provider]["api_key_env"]
            context.config["env"][key_name] = api_key

            # Save immediately
            save_user_config(context.config)

        return SetupResult(success=True, data={"api_keys": api_keys})
```

## Template Configuration

Templates have their own configuration format:

```python
@dataclass
class Template:
    """Template configuration"""
    name: str
    description: str
    prompt: str
    allowed_tools: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    shortcuts: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Template":
        return cls(**data)

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)
```

Template files are stored in `~/.config/tunacode/templates/`:

```json
{
    "name": "refactor_code",
    "description": "Refactor code for better readability",
    "prompt": "Please refactor the following code for better readability: $ARGUMENTS",
    "allowed_tools": ["read_file", "update_file", "grep"],
    "parameters": {
        "style_guide": "PEP8",
        "preserve_functionality": true
    },
    "shortcuts": ["refactor", "rf"]
}
```

## Configuration Commands

### /refresh-config Command

Reload configuration from defaults:

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Refresh configuration from defaults"""

    # Reload from disk
    new_config = load_user_config()

    # Preserve runtime overrides
    if state.state.model_override:
        new_config["default_model"] = state.state.model_override

    # Update state
    state.state.user_config = new_config
    state._update_from_config(new_config)

    await self.ui.success("Configuration refreshed from disk")
```

### /model Command

Update model configuration:

```python
async def execute(self, args: str, state: StateManager) -> None:
    """Change AI model"""

    if not args:
        # Show current model
        current = state.get_model()
        await self.ui.info(f"Current model: {current}")
        return

    # Validate model format
    if ":" not in args:
        await self.ui.error("Format: provider:model-name")
        return

    # Update configuration
    state.update_config({"default_model": args})

    # Update runtime state
    state.state.default_model = args
    state.state.model_override = None  # Clear override

    await self.ui.success(f"Model changed to: {args}")
```

## Best Practices

### 1. Configuration Validation

```python
def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return errors"""
    errors = []

    # Check model format
    if model := config.get("default_model"):
        if ":" not in model:
            errors.append("Invalid model format (expected provider:model)")

    # Check numeric ranges
    if window := config.get("context_window"):
        if not (1000 <= window <= 2000000):
            errors.append("Context window out of range")

    # Check required fields
    if not config.get("env"):
        errors.append("Missing env section")

    return errors
```

### 2. Migration Support

```python
def migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate old config formats"""
    version = config.get("version", "0.0.0")

    # Pre-0.0.50: Move API keys to env section
    if version < "0.0.50":
        for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            if key in config:
                config.setdefault("env", {})[key] = config.pop(key)

    # Pre-0.0.51: Rename model IDs
    if version < "0.0.51":
        if config.get("default_model") == "claude-3-sonnet":
            config["default_model"] = "anthropic:claude-3-5-sonnet-20241022"

    # Update version
    config["version"] = ApplicationSettings.VERSION

    return config
```

### 3. Sensitive Data Handling

```python
def sanitize_config_for_logging(config: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data for logging"""
    sanitized = config.copy()

    # Redact API keys
    if "env" in sanitized:
        for key in sanitized["env"]:
            if "KEY" in key or "TOKEN" in key:
                sanitized["env"][key] = "***REDACTED***"

    # Redact MCP server secrets
    if "mcp_servers" in sanitized:
        for server in sanitized["mcp_servers"].values():
            if "env" in server:
                for key in server["env"]:
                    if "KEY" in key or "TOKEN" in key:
                        server["env"][key] = "***REDACTED***"

    return sanitized
```

## Configuration Schema

Complete configuration schema:

```typescript
interface TunaCodeConfig {
    // Model settings
    default_model: string;          // provider:model format
    context_window: number;         // Max context size
    max_response_tokens: number;    // Max response size
    max_iterations?: number;        // ReAct iteration limit

    // UI settings
    streaming: boolean;             // Enable streaming display
    show_thoughts: boolean;         // Show agent reasoning
    yolo_mode: boolean;            // Skip confirmations

    // Tool settings
    tool_options: {
        auto_approve_reads: boolean;    // Auto-approve read tools
        require_confirmation: boolean;   // Require confirmations
        show_diffs: boolean;            // Show diffs in updates
    };

    // UI options
    ui_options: {
        theme: string;              // UI theme
        show_costs: boolean;        // Display costs
        show_tokens: boolean;       // Display token usage
        show_spinner: boolean;      // Show loading spinner
    };

    // MCP servers
    mcp_servers: {
        [name: string]: {
            command: string;        // Executable command
            args: string[];         // Command arguments
            env?: {                 // Environment variables
                [key: string]: string;
            };
        };
    };

    // Environment variables
    env: {
        [key: string]: string;      // API keys and secrets
    };

    // Version for migration
    version?: string;
}
```

## Future Enhancements

1. **Profiles**: Multiple named configurations
2. **Encryption**: Secure storage of API keys
3. **Remote Config**: Cloud-based configuration sync
4. **Hot Reload**: Configuration changes without restart
5. **Validation UI**: Interactive configuration wizard
