import logging
from fastapi import APIRouter, Request
from app.llm.openai_client import get_ai_response
from app.services.whatsapp import send_whatsapp
from app.memory.redis_memory import save_message

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
    user_message = data["message"]["content"]

    logger.info(f"👤 FROM: {phone}")
    logger.info(f"💬 USER MESSAGE: {user_message}")

    save_message(phone, "USER", user_message)
    reply = get_ai_response(user_message)

    logger.info(f"🤖 BOT REPLY: {reply}")

    save_message(phone, "BOT", reply)
    send_whatsapp(phone=phone, message=reply)

    logger.info(f"✅ REPLY SENT TO: {phone}")
    return {"status": "success"}