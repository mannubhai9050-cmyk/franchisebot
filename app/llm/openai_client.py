import json
import re
from datetime import datetime

import pytz
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

TIMEZONE = "Asia/Kolkata"

LEAD_CACHE_TTL = 3600
LEAD_NEGATIVE_TTL = 600

REGISTER_PATTERN = re.compile(
    r"<REGISTER>(.*?)</REGISTER>",
    re.DOTALL
)

with open(
    "app/prompts/system_prompt.txt",
    "r",
    encoding="utf-8"
) as f:
    SYSTEM_PROMPT = f.read()


def current_time():

    tz = pytz.timezone(TIMEZONE)

    now = datetime.now(tz)

    return now.strftime(
        "%A, %d %B %Y, %I:%M %p IST"
    )


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


def get_lead_profile(phone):

    cache_key = f"lead:{phone}"

    cached = redis_client.get(cache_key)

    if cached is not None:

        data = json.loads(cached)

        return data if data else None

    response = get_lead(phone)

    if response.get("success") and response.get("data"):

        d = response["data"]

        profile = {
            "name": d.get("name", "").strip(),
            "email": d.get("email", ""),
            "phone": d.get("phone", phone),
            "city": d.get("city", "").strip(),
            "investment": d.get("investment", ""),
            "status": d.get("status", ""),
            "plan": d.get("plan", ""),
            "totalAmount": d.get("totalAmount", "")
        }

        redis_client.setex(
            cache_key,
            LEAD_CACHE_TTL,
            json.dumps(profile)
        )

        return profile

    redis_client.setex(
        cache_key,
        LEAD_NEGATIVE_TTL,
        json.dumps({})
    )

    return None


def do_registration(phone, raw_json):

    try:

        details = json.loads(raw_json)

    except json.JSONDecodeError:

        return False, "Details parse nahi hui, user se dobara confirm karo."

    reg_phone = str(
        details.get("phone") or phone
    ).strip()

    payload = {
        "name": str(details.get("name", "")).strip(),
        "email": str(details.get("email", "")).strip(),
        "phone": reg_phone,
        "leadType": "chatbot",
        "city": str(details.get("city", "")).strip(),
        "investment": str(details.get("investment", "0")).strip(),
        "totalAmount": 500000
    }

    missing = [
        field
        for field in ("name", "email", "city")
        if not payload[field]
    ]

    if missing:

        return False, f"Ye details missing hain: {', '.join(missing)}. User se pucho."

    result = create_lead(payload)

    if result.get("success"):

        redis_client.delete(f"lead:{phone}")
        redis_client.delete(f"lead:{reg_phone}")

        return True, payload

    return False, "API se booking fail ho gayi, user ko politely batao ki team contact karegi."


def build_user_context(phone, profile):

    if profile:

        profile_block = f"""## REGISTERED USER (already booked - DO NOT re-register)
- Name: {profile['name']}
- City: {profile['city']}
- Plan: {profile['plan']}
- Booking status: {profile['status']}
- Total amount: {profile['totalAmount']}

Rules:
- Greet and address them by their FIRST NAME naturally.
- Never ask for name/city/budget again, you already know it.
- Never start registration again.
- Help with their questions, booking status, and next steps."""

    else:

        profile_block = f"""## NEW USER (not registered yet)
If the user wants to book / register the franchise:
1. Collect ONE detail at a time: name, email, city, investment amount.
2. Then ask: registration ke liye yahi WhatsApp number ({phone}) use karna hai ya koi aur number dena chahenge?
3. Show a short summary and ask for final confirmation.
4. ONLY after user confirms everything, reply with EXACTLY this tag and NOTHING else:
<REGISTER>{{"name": "...", "email": "...", "phone": "...", "city": "...", "investment": "..."}}</REGISTER>
5. Never show or mention this tag to the user."""

    return f"""# USER CONTEXT
Current date & time: {current_time()}
User WhatsApp number: {phone}

{profile_block}"""


def ask_model(user_context, conversation, knowledge, message):

    prompt = f"""
{user_context}

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

    return response.output_text or ""


def get_ai_response(phone, message):

    profile = get_lead_profile(phone)

    history = get_history(phone)

    conversation = "\n".join(history)

    knowledge = ""

    if need_rag(message):

        knowledge = search_knowledge(
            message
        )

    user_context = build_user_context(
        phone,
        profile
    )

    text = ask_model(
        user_context,
        conversation,
        knowledge,
        message
    )

    match = REGISTER_PATTERN.search(text)

    if not match:

        return text

    # ---- Registration triggered ----

    success, result = do_registration(
        phone,
        match.group(1)
    )

    if success:

        system_note = f"""# SYSTEM EVENT
Registration SUCCESSFUL. Details saved:
{json.dumps(result, ensure_ascii=False)}

Congratulate the user warmly in your normal style, confirm their details briefly, and tell them the team will contact them soon. Do NOT use any tag."""

    else:

        system_note = f"""# SYSTEM EVENT
Registration FAILED. Reason: {result}

Respond to the user accordingly in your normal style. Do NOT use any tag."""

    final_context = f"{user_context}\n\n{system_note}"

    reply = ask_model(
        final_context,
        conversation,
        knowledge,
        message
    )

    # safety: strip tag if model ever repeats it
    return REGISTER_PATTERN.sub("", reply).strip()