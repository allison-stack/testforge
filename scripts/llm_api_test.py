import os

from dotenv import load_dotenv
from openrouter import OpenRouter

load_dotenv()

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    response = client.chat.send(
        model="openai/gpt-oss-120b:free",
        messages=[{"role": "user", "content": "What is the meaning of life?"}],
    )

print(response.choices[0].message.content)
