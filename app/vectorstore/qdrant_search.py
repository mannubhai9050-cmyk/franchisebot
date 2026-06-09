from qdrant_client import QdrantClient
from openai import OpenAI

from app.config import (
    OPENAI_API_KEY,
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)


def embed_query(query: str):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    return response.data[0].embedding


def search_knowledge(query: str) -> str:
    vector = embed_query(query)

    response = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=5,
    )

    context = []
    for point in response.points:
        payload = point.payload or {}
        if "text" in payload:
            context.append(payload["text"])

    return "\n".join(context)