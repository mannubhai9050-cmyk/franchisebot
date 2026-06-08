from fastapi import APIRouter
from fastapi import Request

from app.llm.openai_client import get_ai_response
from app.services.whatsapp import send_whatsapp

from app.memory.redis_memory import (
    save_message
)

router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    if data.get("event") != "message.received":
        return {"status": "ignored"}

    phone = data["contact"]["phone"]

    user_message = data["message"]["content"]

    save_message(
        phone,
        "USER",
        user_message
    )

    reply = get_ai_response(
        user_message
    )

    save_message(
        phone,
        "BOT",
        reply
    )

    send_whatsapp(
        phone=phone,
        message=reply
    )

    return {
        "status": "success"
    }