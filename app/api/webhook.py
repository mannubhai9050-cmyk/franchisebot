import logging
from fastapi import APIRouter
from fastapi import Request

from app.llm.openai_client import get_ai_response
from app.services.whatsapp import send_whatsapp

from app.memory.redis_memory import (
    save_message
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhook")
async def webhook(request: Request):

    data = await request.json()

    logger.info(f"📩 WEBHOOK RECEIVED: {data}")

    if data.get("event") != "message.received":
        logger.info(f"⏭️ IGNORED EVENT: {data.get('event')}")
        return {"status": "ignored"}

    phone = data["contact"]["phone"]
    workspace_id = data.get("workspace_id")
    user_message = data["message"]["content"]

    logger.info(f"👤 FROM: {phone} | WORKSPACE: {workspace_id}")
    logger.info(f"💬 USER MESSAGE: {user_message}")

    save_message(
        phone,
        "USER",
        user_message
    )

    reply = get_ai_response(
        user_message
    )

    logger.info(f"🤖 BOT REPLY: {reply}")

    save_message(
        phone,
        "BOT",
        reply
    )

    send_whatsapp(
        phone=phone,
        message=reply,
        workspace_id=workspace_id
    )

    logger.info(f"✅ REPLY SENT TO: {phone} | WORKSPACE: {workspace_id}")

    return {
        "status": "success"
    }