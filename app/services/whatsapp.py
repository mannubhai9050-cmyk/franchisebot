import requests

from app.config import WHATSAPP_API_KEY

URL = "https://whatsapp.limbu.ai/api/external/send"


def send_whatsapp(phone, message):

    headers = {
        "X-API-Key": WHATSAPP_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "phone": phone,
        "message": message
    }

    r = requests.post(
        URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    print(r.text)

    return True