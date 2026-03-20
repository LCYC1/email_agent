from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
import os
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

llm = ChatAnthropic(model="claude-haiku-4-5-20251001")
response = llm.invoke("Say hello world")
print(response.content)
