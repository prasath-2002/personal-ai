from openai import OpenAI

from app.core.config import OPENAI_API_KEY, OPENAI_MODEL

from app.services.database_service import (
    clear_messages,
    get_messages,
    save_message,
)

client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_INSTRUCTIONS = """
You are a private personal AI assistant.

The user may communicate in Tamil, English, or Tanglish.
Understand mixed Tamil-English naturally.
Respond in the user's preferred language and style.
Be clear, accurate, and practical.
"""


def generate_response(session_id: str, message: str) -> str:
    save_message(session_id, "user", message)

    conversation_history = get_messages(session_id)

    response = client.responses.create(
        model=OPENAI_MODEL,
        instructions=SYSTEM_INSTRUCTIONS,
        input=conversation_history,
    )

    ai_text = response.output_text

    save_message(session_id, "assistant", ai_text)

    return ai_text

def reset_conversation(session_id: str) -> None:
    clear_messages(session_id)

