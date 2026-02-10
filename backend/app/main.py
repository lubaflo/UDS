from __future__ import annotations

from fastapi import FastAPI

from app.api.v1 import router as v1_router

app = FastAPI(title="UDS admin backend", version="0.1.0")

app.include_router(v1_router)


@app.get("/")
async def health() -> dict:
    return {"status": "ok"}