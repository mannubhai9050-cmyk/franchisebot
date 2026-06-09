import logging
import requests

from app.config import WHATSAPP_API_KEY

logger = logging.getLogger(__name__)

URL = "https://whatsapp.limbu.ai/api/external/send"


def send_whatsapp(phone, message, workspace_id=None):

    headers = {
        "X-API-Key": WHATSAPP_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "phone": phone,
        "message": message,
    }

    if workspace_id:
        payload["workspace_id"] = workspace_id

    logger.info(f"📤 SENDING WHATSAPP | PHONE: {phone} | WORKSPACE: {workspace_id}")
    logger.info(f"📦 PAYLOAD: {payload}")

    r = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    logger.info(f"📬 WHATSAPP API RESPONSE: {r.text}")

    return True