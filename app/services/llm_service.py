from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_INSTRUCTIONS = """
You are a private personal AI assistant.

The user may communicate in Tamil, English, or Tanglish.
Understand mixed Tamil-English naturally.
Respond in the user's preferred language and style.
Be clear, accurate, and practical.
"""


def generate_response(message: str) -> str:
    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=message,
    )

    return response.output_text