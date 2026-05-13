from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from backend.core.config import get_settings


class OpenAIProvider:
    def __init__(self, model_name: str):
        self.model_name = model_name
        settings = get_settings()
        self.api_key = settings.openai_api_key or ""

    def get_model(self, temperature: float = 0.0) -> BaseChatModel:
        return ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            api_key=self.api_key,
        )

    async def generate(self, prompt: str, system_prompt: str) -> str:
        model = self.get_model(temperature=0.0)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
        resp = await model.ainvoke(messages)
        return str(resp.content)
