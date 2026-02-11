from __future__ import annotations

from fastapi import APIRouter

from app.db.session import db_healthcheck

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict:
    return {"status": "ok", "db": "ok" if db_healthcheck() else "fail"}
