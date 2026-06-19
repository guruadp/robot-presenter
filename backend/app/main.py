import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    settings = get_settings()
    for path in (
        settings.STORAGE_DIR,
        settings.CHROMA_DIR,
        os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")),
    ):
        if path:
            os.makedirs(path, exist_ok=True)
    logging.basicConfig(level=settings.LOG_LEVEL)
    yield


app = FastAPI(title="Ednex AI Presenter", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ednex-ai-presenter"}
