from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, health
from app.api.v1.admin import clients, messages, security

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(health.router)

router.include_router(clients.router)
router.include_router(messages.router)
router.include_router(security.router)