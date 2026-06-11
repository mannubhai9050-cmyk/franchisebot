from qdrant_client import QdrantClient
from openai import OpenAI

from app.config import (
    OPENAI_API_KEY,
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME,
)

from app.memory.redis_memory import (
    redis_client
)

openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def embed_query(query):

    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )

    return response.data[0].embedding


def search_knowledge(query):

    cache_key = f"rag:{query.lower()}"

    cached = redis_client.get(
        cache_key
    )

    if cached:

        print("✅ CACHE HIT")

        return cached

    print("🔍 QDRANT SEARCH")

    vector = embed_query(query)

    response = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=3
    )

    context = []

    for point in response.points:

        payload = point.payload or {}

        if "text" in payload:

            context.append(
                payload["text"]
            )

    result = "\n".join(context)

    redis_client.setex(
        cache_key,
        86400,
        result
    )

    return result