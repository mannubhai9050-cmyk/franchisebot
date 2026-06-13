import logging
from datetime import datetime

from app.memory.redis_memory import (
    redis_client,
    get_history,
    save_message
)

from app.llm.openai_client import (
    ask_model,
    build_user_context,
    get_lead_profile
)

from app.services.whatsapp import send_whatsapp

logger = logging.getLogger(__name__)

FOLLOWUP_AFTER = 4 * 3600     # 4 hours inactive
MAX_FOLLOWUPS = 2             # max follow-ups per user


def run_followups():

    now = datetime.now().timestamp()

    for key in redis_client.scan_iter("last_active:*"):

        phone = key.split(":", 1)[1]

        last = float(redis_client.get(key) or 0)

        if now - last < FOLLOWUP_AFTER:
            continue

        count = int(
            redis_client.get(f"followup_count:{phone}") or 0
        )

        if count >= MAX_FOLLOWUPS:
            continue

        try:

            send_followup(phone, count)

        except Exception as e:

            logger.error(f"Followup failed for {phone}: {e}")


def send_followup(phone, count):

    history = get_history(phone)

    if not history:
        return

    conversation = "\n".join(history)

    profile = get_lead_profile(phone)

    user_context = build_user_context(phone, profile)

    system_note = f"""# SYSTEM EVENT
The user has been INACTIVE for a few hours. This is follow-up number {count + 1}.
Send ONE short, friendly, natural follow-up message in your style based on where the conversation stopped.
Goal: re-engage them towards the next step (answer pending question / discovery call / registration).
Do not repeat old messages. Do not use any tag. Keep it 1-2 lines."""

    reply = ask_model(
        f"{user_context}\n\n{system_note}",
        conversation,
        "",
        "(no new message - send follow-up)"
    )

    reply = reply.strip()

    if not reply:
        return

    send_whatsapp(phone, reply)

    save_message(phone, "assistant", reply)

    redis_client.set(
        f"followup_count:{phone}",
        count + 1
    )

    redis_client.set(
        f"last_active:{phone}",
        datetime.now().timestamp()
    )

    logger.info(f"📨 FOLLOWUP {count + 1} SENT | {phone}")