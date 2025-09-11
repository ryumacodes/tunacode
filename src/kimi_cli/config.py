import json
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, Field, SecretStr, ValidationError, model_validator


class LLMProvider(BaseModel):
    """LLM provider configuration."""

    type: Literal["kimi", "openai_legacy"] = Field(..., description="Provider type")
    base_url: str = Field(..., description="API base URL")
    api_key: SecretStr = Field(..., description="API key")


class LLMModel(BaseModel):
    """LLM model configuration."""

    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model name")


class Config(BaseModel):
    """Main configuration structure."""

    default_model: str | None = Field(None, description="Default model to use")
    models: dict[str, LLMModel] = Field(default_factory=dict, description="List of LLM models")
    providers: dict[str, LLMProvider] = Field(
        default_factory=dict, description="List of LLM providers"
    )

    @model_validator(mode="after")
    def validate_model(self) -> Self:
        if self.default_model and self.default_model not in self.models:
            raise ValueError(f"Default model {self.default_model} not found in models")
        for model in self.models.values():
            if model.provider not in self.providers:
                raise ValueError(f"Provider {model.provider} not found in providers")
        return self


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    config_dir = Path.home() / ".config" / "kimi"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_share_dir() -> Path:
    """Get the shared directory path."""
    share_dir = Path.home() / ".local" / "share" / "kimi"
    share_dir.mkdir(parents=True, exist_ok=True)
    return share_dir


def get_config_file_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.json"


DEFAULT_KIMI_MODEL = "kimi-k2-turbo-preview"
DEFAULT_KIMI_BASE_URL = "https://api.moonshot.cn/v1"


def get_default_config() -> Config:
    """Get the default configuration."""
    return Config(
        default_model=DEFAULT_KIMI_MODEL,
        models={
            DEFAULT_KIMI_MODEL: LLMModel(provider="kimi", model=DEFAULT_KIMI_MODEL),
        },
        providers={
            "kimi": LLMProvider(
                type="kimi",
                base_url=DEFAULT_KIMI_BASE_URL,
                api_key=SecretStr("<your-api-key>"),
            ),
        },
    )


def load_config() -> Config:
    """Load configuration from ~/.config/kimi/config.json.

    Returns:
        Validated Config object.
    """
    config_file = get_config_file_path()

    if not config_file.exists():
        config = get_default_config()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2)
        return config

    try:
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        return Config(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ConfigError(f"Invalid configuration file: {config_file}") from e


class ConfigError(Exception):
    """Configuration error."""

    def __init__(self, message: str):
        super().__init__(message)
