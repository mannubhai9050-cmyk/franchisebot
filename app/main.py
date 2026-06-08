from fastapi import FastAPI

from app.api.webhook import router

app = FastAPI()

app.include_router(router)


@app.get("/")
def home():

    return {
        "status": "running",
        "project": "Limbu AI Franchise Bot"
    }