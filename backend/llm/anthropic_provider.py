import asyncio

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings


class AnthropicProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name
        settings = get_settings()
        self.api_key = settings.anthropic_api_key or ""

    def get_model(self, temperature: float = 0.0) -> BaseChatModel:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:
            raise RuntimeError("Install langchain-anthropic for Anthropic support") from e
        return ChatAnthropic(
            model=self.model_name,
            temperature=temperature,
            api_key=self.api_key,
            timeout=60,
            max_retries=1,
        )

    async def generate(self, prompt: str, system_prompt: str) -> str:
        model = self.get_model(temperature=0.0)
        messages = [HumanMessage(content=f"{system_prompt}\n\n{prompt}")]
        resp = await asyncio.wait_for(model.ainvoke(messages), timeout=60)
        return str(resp.content)
