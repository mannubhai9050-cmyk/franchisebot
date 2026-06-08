import redis

from app.config import REDIS_URL

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)


def save_message(phone, role, message):

    key = f"chat:{phone}"

    redis_client.rpush(
        key,
        f"{role}: {message}"
    )


def get_history(phone):

    key = f"chat:{phone}"

    return redis_client.lrange(
        key,
        0,
        -1
    )