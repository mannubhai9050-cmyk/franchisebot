import json
import re

from openai import OpenAI

from app.config import OPENAI_API_KEY

from app.vectorstore.qdrant_search import (
    search_knowledge
)

from app.memory.redis_memory import (
    get_history,
    redis_client
)

from app.services.franchise_api import (
    get_lead,
    create_lead
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

REGISTER_PATTERN = re.compile(
    r"\{[\s\S]*?\}"
)


def clean_phone(phone):
    return re.sub(r"\D", "", str(phone))[-10:]


def need_rag(message):

    msg = message.lower()

    keywords = [
        "franchise",
        "investment",
        "cost",
        "fee",
        "price",
        "profit",
        "training",
        "support",
        "royalty",
        "business",
        "google",
        "seo",
        "maps",
        "gmb"
    ]

    return any(
        word in msg
        for word in keywords
    )


def get_lead_profile(phone):

    cache_key = f"lead:{phone}"

    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    result = get_lead(phone)

    if (
        result.get("success")
        and result.get("data")
    ):
        profile = result["data"]

        redis_client.setex(
            cache_key,
            3600,
            json.dumps(profile)
        )

        return profile

    return None


def create_registration(phone, raw_json):

    try:
        data = json.loads(raw_json)

    except Exception:
        return False

    payload = {
        "name": data["name"],
        "email": data["email"],
        "phone": data.get("phone", phone),
        "city": data["city"],
        "investment": data["investment"],
        "leadType": "chatbot",
        "totalAmount": 500000
    }

    result = create_lead(payload)

    return result.get("success", False)


def get_ai_response(phone, message):

    profile = get_lead_profile(
        clean_phone(phone)
    )

    history = get_history(phone)

    conversation = "\n".join(
        history[-10:]
    )

    knowledge = ""

    if need_rag(message):

        knowledge = search_knowledge(
            message
        )

    profile_text = ""

    if profile:

        profile_text = f"""
Registered User:

Name: {profile.get('name')}
City: {profile.get('city')}
Plan: {profile.get('plan')}
Status: {profile.get('status')}
"""

    prompt = f"""
{profile_text}

Conversation:
{conversation}

Knowledge:
{knowledge}

User:
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

    text = response.output_text

    match = REGISTER_PATTERN.search(
        text
    )

    if match:

        if create_registration(
            phone,
            match.group()
        ):

            return (
                "🎉 Your franchise enquiry has been registered successfully. "
                "Our team will contact you shortly."
            )

    return text