import os

from kosong.base.chat_provider import ChatProvider
from kosong.chat_provider import Kimi, OpenAILegacy
from pydantic import SecretStr

from kimi_cli.config import LLMModel, LLMProvider


def augment_provider_with_env_vars(provider: LLMProvider):
    match provider.type:
        case "kimi":
            if base_url := os.getenv("KIMI_BASE_URL"):
                provider.base_url = base_url
            if api_key := os.getenv("KIMI_API_KEY"):
                provider.api_key = SecretStr(api_key)
        case "openai_legacy":
            if base_url := os.getenv("OPENAI_BASE_URL"):
                provider.base_url = base_url
            if api_key := os.getenv("OPENAI_API_KEY"):
                provider.api_key = SecretStr(api_key)
        case _:
            raise ValueError(f"Unsupported provider: {provider.type}")


def create_chat_provider(provider: LLMProvider, model: LLMModel) -> ChatProvider:
    match provider.type:
        case "kimi":
            return Kimi(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
            )
        case "openai_legacy":
            return OpenAILegacy(
                model=model.model,
                base_url=provider.base_url,
                api_key=provider.api_key.get_secret_value(),
            )
        case _:
            raise ValueError(f"Unsupported provider: {provider.type}")
