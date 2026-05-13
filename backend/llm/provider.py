"""LLM provider protocol and factory."""

from typing import Protocol, runtime_checkable

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage


@runtime_checkable
class LLMProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: str) -> str: ...

    def get_model(self, temperature: float = 0.0) -> BaseChatModel: ...


def get_llm_provider(provider_type: str, model_name: str) -> LLMProvider:
    t = provider_type.lower()
    if t == "openrouter":
        from backend.llm.openrouter_provider import OpenRouterProvider

        return OpenRouterProvider(model_name)
    if t == "openai":
        from backend.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(model_name)
    if t == "anthropic":
        from backend.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(model_name)
    raise ValueError(f"Unknown provider type: {provider_type}")
