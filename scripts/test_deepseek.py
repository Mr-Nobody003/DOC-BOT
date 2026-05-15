import asyncio
from langchain_openai import ChatOpenAI

async def test():
    from backend.core.config import get_settings
    settings = get_settings()
    llm = ChatOpenAI(
        model="deepseek/deepseek-v4-flash:free",
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    
    print("Testing DeepSeek Flash Text Output...")
    try:
        res = await asyncio.wait_for(llm.ainvoke("Say hello"), timeout=5)
        print("Success:", res.content)
    except Exception as e:
        print("Error:", type(e), str(e))

if __name__ == "__main__":
    asyncio.run(test())
