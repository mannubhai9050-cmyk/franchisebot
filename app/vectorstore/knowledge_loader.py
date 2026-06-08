from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from openai import OpenAI
import uuid

from app.config import (
    OPENAI_API_KEY,
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME
)

client = OpenAI(
    api_key=OPENAI_API_KEY
)

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

EMBED_MODEL = "text-embedding-3-small"


def create_collection():

    collections = qdrant.get_collections()

    names = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME not in names:

        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )

        print("Collection created")

    else:

        print("Collection already exists")


def get_embedding(text):

    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text
    )

    return response.data[0].embedding


def chunk_text(text, size=1000):

    chunks = []

    for i in range(
        0,
        len(text),
        size
    ):

        chunks.append(
            text[i:i + size]
        )

    return chunks


def upload_file(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        text = f.read()

    chunks = chunk_text(text)

    points = []

    for chunk in chunks:

        vector = get_embedding(chunk)

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": chunk
                }
            )
        )

    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(
        f"Uploaded {len(points)} chunks"
    )


if __name__ == "__main__":

    create_collection()

    upload_file(
        "app/knowledge/limbu_ai_master.txt"
    )