from openai import OpenAI

from app.config import OPENAI_API_KEY

from app.vectorstore.qdrant_search import (
    search_knowledge
)

from app.memory.redis_memory import (
    get_history
)

client = OpenAI(
    api_key=OPENAI_API_KEY
)

with open(
    "app/prompts/system_prompt.txt",
    "r",
    encoding="utf-8"
) as f:

    SYSTEM_PROMPT = f.read()


def need_rag(message):

    message = message.lower()

    keywords = [
        "franchise",
        "fee",
        "cost",
        "price",
        "investment",
        "profit",
        "location",
        "requirement",
        "document",
        "training",
        "royalty"
    ]

    return any(
        word in message
        for word in keywords
    )


def get_ai_response(phone, message):

    history = get_history(phone)

    conversation = "\n".join(history)

    knowledge = ""

    if need_rag(message):

        knowledge = search_knowledge(
            message
        )

    prompt = f"""
Conversation History:

{conversation}

Knowledge Base:

{knowledge}

Current User Question:

{message}
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.output_text