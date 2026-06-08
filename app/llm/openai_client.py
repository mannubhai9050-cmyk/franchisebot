from openai import OpenAI

from app.config import OPENAI_API_KEY

from app.vectorstore.qdrant_search import (
    search_knowledge
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


def get_ai_response(message):

    knowledge = search_knowledge(
        message
    )

    prompt = f"""
Knowledge Base:

{knowledge}

User Question:

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