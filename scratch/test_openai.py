import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print("API Key present:", bool(api_key))

client = OpenAI(api_key=api_key)

try:
    response = client.models.list()
    print("OpenAI models retrieved successfully:", [m.id for m in list(response)[:5]])
except Exception as e:
    print("Error listing models:", e)
