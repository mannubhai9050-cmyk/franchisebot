import logging
from fastapi import FastAPI
from app.api.webhook import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

app = FastAPI()
app.include_router(router)


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "Limbu AI Franchise Bot"
    }