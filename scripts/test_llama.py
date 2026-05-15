import asyncio
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

class TestOutput(BaseModel):
    intent: str = Field(description="The intent")
    score: int = Field(description="A score from 1-10")

async def test():
    from backend.core.config import get_settings
    settings = get_settings()
    llm = ChatOpenAI(
        model="meta-llama/llama-3.3-70b-instruct:free",
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    
    structured = llm.with_structured_output(TestOutput)
    
    print("Testing Llama 3.3 70B Instruct...")
    try:
        res = await asyncio.wait_for(structured.ainvoke("What is the intent of 'I have a headache' and score it?"), timeout=20)
        print("Success:", res)
    except Exception as e:
        print("Error:", type(e), str(e))

if __name__ == "__main__":
    asyncio.run(test())
