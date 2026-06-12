import logging

from fastapi import APIRouter, Request

from app.llm.openai_client import (
    get_ai_response
)

from app.services.whatsapp import (
    send_whatsapp
)

from app.memory.redis_memory import (
    save_message,
    get_history
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    logger.info(
        f"WEBHOOK RECEIVED: {data}"
    )

    if data.get("event") != "message.received":

        return {
            "status": "ignored"
        }

    phone = data["contact"]["phone"]

    user_message = data["message"]["content"]

    save_message(
        phone,
        "USER",
        user_message
    )

    reply = get_ai_response(
        phone,
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

@router.get("/history/{phone}")
def history(phone: str):
    return {
        "phone": phone,
        "history": get_history(phone)
    }