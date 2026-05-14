import asyncio
import os
from backend.llm.openrouter_provider import OpenRouterProvider
from backend.core.config import get_settings

async def test_llm():
    settings = get_settings()
    print("API Key loaded:", settings.openrouter_api_key[:10] + "..." if settings.openrouter_api_key else "None")
    print("Model:", settings.llm_model_generation)
    
    provider = OpenRouterProvider(settings.llm_model_generation)
    
    try:
        response = await provider.generate("Say 'Hello, World!'", "You are a helpful assistant.")
        print("Success! Response:", response)
    except Exception as e:
        print("Exception occurred:", type(e).__name__)
        print(e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
