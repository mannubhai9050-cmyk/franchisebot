import requests

BASE_URL = "https://limbu.ai/api/franchise"


def get_lead(phone):

    try:

        response = requests.get(
            f"{BASE_URL}?phoneNumber={phone}",
            timeout=20
        )

        return response.json()

    except Exception as e:

        print(e)

        return {
            "success": False
        }


def create_lead(payload):

    response = requests.post(
        BASE_URL,
        json=payload,
        timeout=20
    )

    return response.json()