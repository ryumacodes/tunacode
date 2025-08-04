<!-- This document details the API for configuration: settings management, model configuration, and user preferences -->

# Configuration API Reference

This document provides detailed API documentation for TunaCode's configuration system.

## Settings Module

`tunacode.configuration.settings`

Core application settings and constants.

### PathConfig

```python
@dataclass(frozen=True)
class PathConfig:
    """Configuration file paths."""

    CONFIG_DIR: Path = Path.home() / ".config" / "tunacode"
    CONFIG_FILE: Path = CONFIG_DIR / "tunacode.json"
    TEMPLATES_DIR: Path = CONFIG_DIR / "templates"
    LOGS_DIR: Path = CONFIG_DIR / "logs"

    @classmethod
    def ensure_directories(cls) -> None:
        """Create all required directories."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

### ApplicationSettings

```python
@dataclass(frozen=True)
class ApplicationSettings:
    """Core application settings."""

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
    MAX_PARALLEL_TOOLS: int = field(
        default_factory=lambda: int(
            os.environ.get("TUNACODE_MAX_PARALLEL", str(os.cpu_count() or 4))
        )
    )

    # Context limits
    DEFAULT_CONTEXT_WINDOW: int = 200000
    DEFAULT_MAX_RESPONSE_TOKENS: int = 4096
    DEFAULT_MAX_ITERATIONS: int = 10

    # File limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_GLOB_RESULTS: int = 10000
```

## Defaults Module

`tunacode.configuration.defaults`

Default configuration values.

### DEFAULT_CONFIG

```python
DEFAULT_CONFIG: Dict[str, Any] = {
    # Model settings
    "default_model": "anthropic:claude-3-5-sonnet-20241022",
    "context_window": 200000,
    "max_response_tokens": 4096,
    "max_iterations": 10,

    # UI settings
    "streaming": True,
    "show_thoughts": False,
    "yolo_mode": False,

    # Tool settings
    "tool_options": {
        "auto_approve_reads": False,
        "require_confirmation": True,
        "show_diffs": True
    },

    # UI options
    "ui_options": {
        "theme": "default",
        "show_costs": True,
        "show_tokens": True,
        "show_spinner": True
    },

    # MCP servers
    "mcp_servers": {},

    # Environment variables
    "env": {
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
        # ... other API keys ...
    }
}
```

### Functions

#### get_default_config()
```python
def get_default_config() -> Dict[str, Any]:
    """
    Get a copy of default configuration.

    Returns:
        Dict[str, Any]: Deep copy of defaults

    Example:
        >>> config = get_default_config()
        >>> config["default_model"] = "openai:gpt-4"
    """
```

## Models Module

`tunacode.configuration.models`

Model registry and pricing information.

### ModelInfo

```python
@dataclass
class ModelInfo:
    """Model metadata and pricing."""

    provider: str
    name: str
    display_name: str
    context_window: int
    max_output_tokens: int
    supports_tools: bool
    supports_vision: bool
    input_price_per_million: float  # USD
    output_price_per_million: float # USD

    @property
    def model_id(self) -> str:
        """Get full model identifier."""
        return f"{self.provider}:{self.name}"

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost for token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            float: Cost in USD

        Example:
            >>> model.calculate_cost(1000, 500)
            0.0045
        """
```

### MODEL_REGISTRY

```python
MODEL_REGISTRY: Dict[str, ModelInfo] = {
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
    # ... more models ...
}
```

### PROVIDER_CONFIGS

```python
PROVIDER_CONFIGS: Dict[str, ProviderConfig] = {
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "requires_api_key": True,
        "base_url": None,
        "timeout": 600
    },
    # ... more providers ...
}
```

### Functions

#### get_model_info()
```python
def get_model_info(model_id: str) -> Optional[ModelInfo]:
    """
    Get model information by ID.

    Args:
        model_id: Model identifier (provider:model)

    Returns:
        Optional[ModelInfo]: Model info or None

    Example:
        >>> info = get_model_info("openai:gpt-4")
        >>> print(info.context_window)
        128000
    """
```

#### get_available_models()
```python
def get_available_models(
    provider: Optional[str] = None,
    supports_tools: Optional[bool] = None
) -> List[ModelInfo]:
    """
    Get filtered list of models.

    Args:
        provider: Filter by provider
        supports_tools: Filter by tool support

    Returns:
        List[ModelInfo]: Matching models

    Example:
        >>> models = get_available_models(provider="anthropic")
    """
```

#### validate_model_id()
```python
def validate_model_id(model_id: str) -> bool:
    """
    Validate model ID format.

    Args:
        model_id: Model identifier to validate

    Returns:
        bool: Whether format is valid

    Example:
        >>> validate_model_id("openai:gpt-4")
        True
        >>> validate_model_id("gpt-4")
        False
    """
```

## User Configuration

`tunacode.utils.user_configuration`

User configuration file management.

### load_user_config()
```python
def load_user_config() -> Dict[str, Any]:
    """
    Load user configuration from disk.

    Returns:
        Dict[str, Any]: Merged configuration

    Note:
        Merges with defaults and applies env overrides.

    Example:
        >>> config = load_user_config()
        >>> print(config["default_model"])
    """
```

### save_user_config()
```python
def save_user_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to disk.

    Args:
        config: Configuration to save

    Raises:
        IOError: If save fails

    Example:
        >>> config["streaming"] = False
        >>> save_user_config(config)
    """
```

### update_user_config()
```python
def update_user_config(updates: Dict[str, Any]) -> None:
    """
    Update specific configuration values.

    Args:
        updates: Key-value pairs to update

    Example:
        >>> update_user_config({
        ...     "default_model": "openai:gpt-4",
        ...     "streaming": False
        ... })
    """
```

### deep_merge()
```python
def deep_merge(base: Dict, updates: Dict) -> Dict:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        updates: Updates to apply

    Returns:
        Dict: Merged dictionary

    Example:
        >>> base = {"a": {"b": 1}}
        >>> updates = {"a": {"c": 2}}
        >>> deep_merge(base, updates)
        {"a": {"b": 1, "c": 2}}
    """
```

### apply_env_overrides()
```python
def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides.

    Args:
        config: Base configuration

    Returns:
        Dict[str, Any]: Config with overrides

    Environment Variables:
        TUNACODE_MODEL: Override default model
        TUNACODE_YOLO: Enable YOLO mode
        TUNACODE_NO_STREAMING: Disable streaming
        TUNACODE_MAX_PARALLEL: Max parallel tools
    """
```

## Configuration Schema

### ConfigurationSchema

```python
class ConfigurationSchema:
    """Configuration validation schema."""

    @staticmethod
    def validate(config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration.

        Args:
            config: Configuration to validate

        Returns:
            List[str]: List of validation errors

        Example:
            >>> errors = ConfigurationSchema.validate(config)
            >>> if errors:
            ...     print("Invalid:", errors)
        """

    @staticmethod
    def migrate(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate old config formats.

        Args:
            config: Configuration to migrate

        Returns:
            Dict[str, Any]: Migrated configuration
        """
```

## MCP Server Configuration

### MCPServerConfig

```python
@dataclass
class MCPServerConfig:
    """MCP server configuration."""

    command: str
    args: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    auto_restart: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary."""
```

## API Key Management

### validate_api_keys()
```python
def validate_api_keys(
    config: Dict[str, Any]
) -> Dict[str, Optional[str]]:
    """
    Validate and return available API keys.

    Args:
        config: Configuration with env section

    Returns:
        Dict[str, Optional[str]]: Provider -> key mapping

    Example:
        >>> keys = validate_api_keys(config)
        >>> if keys["anthropic"]:
        ...     print("Anthropic API key found")
    """
```

### get_api_key()
```python
def get_api_key(
    provider: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Get API key for provider.

    Args:
        provider: Provider name
        config: Optional configuration

    Returns:
        Optional[str]: API key or None

    Note:
        Checks config first, then environment.
    """
```

## Template Configuration

### TemplateConfig

```python
@dataclass
class TemplateConfig:
    """Template configuration."""

    name: str
    description: str
    prompt: str
    allowed_tools: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    shortcuts: List[str] = field(default_factory=list)

    def validate(self) -> List[str]:
        """Validate template configuration."""

    def to_json(self) -> str:
        """Convert to JSON string."""

    @classmethod
    def from_json(cls, json_str: str) -> "TemplateConfig":
        """Create from JSON string."""
```

## Usage Examples

### Basic Configuration

```python
from tunacode.configuration import (
    load_user_config,
    save_user_config,
    get_model_info
)

# Load configuration
config = load_user_config()

# Update model
config["default_model"] = "openai:gpt-4o"

# Get model info
model_info = get_model_info(config["default_model"])
print(f"Context window: {model_info.context_window}")

# Save changes
save_user_config(config)
```

### Model Selection

```python
from tunacode.configuration.models import (
    get_available_models,
    MODEL_REGISTRY
)

# Get all Anthropic models
anthropic_models = get_available_models(provider="anthropic")

# Get models that support tools
tool_models = get_available_models(supports_tools=True)

# Calculate costs
model = MODEL_REGISTRY["openai:gpt-4o"]
cost = model.calculate_cost(
    input_tokens=1000,
    output_tokens=500
)
print(f"Cost: ${cost:.4f}")
```

### Environment Overrides

```python
import os

# Set environment overrides
os.environ["TUNACODE_MODEL"] = "anthropic:claude-3-opus"
os.environ["TUNACODE_YOLO"] = "true"

# Load config with overrides
config = load_user_config()
assert config["default_model"] == "anthropic:claude-3-opus"
assert config["yolo_mode"] is True
```

### MCP Configuration

```python
# Add MCP server
config = load_user_config()
config["mcp_servers"]["my-server"] = {
    "command": "python",
    "args": ["my_server.py"],
    "env": {
        "API_KEY": "${MY_API_KEY}"
    }
}
save_user_config(config)
```

## Configuration Best Practices

### 1. Validation

Always validate configuration after loading:

```python
config = load_user_config()
errors = ConfigurationSchema.validate(config)
if errors:
    for error in errors:
        logger.warning(f"Config error: {error}")
```

### 2. Safe Updates

Use update functions for partial changes:

```python
# Good
update_user_config({"streaming": False})

# Avoid
config = load_user_config()
config["streaming"] = False
save_user_config(config)  # Might overwrite concurrent changes
```

### 3. API Key Security

Never log or display API keys:

```python
def log_config(config: Dict[str, Any]) -> None:
    """Log configuration safely."""
    safe_config = config.copy()
    if "env" in safe_config:
        for key in safe_config["env"]:
            if "KEY" in key or "TOKEN" in key:
                safe_config["env"][key] = "***REDACTED***"
    logger.info(f"Configuration: {safe_config}")
```
