from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY")

REDIS_URL = os.getenv("REDIS_URL")

QDRANT_URL = os.getenv("QDRANT_URL")

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "limbu_franchise")