from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import auth, feedback as app_feedback, health
from app.api.v1.admin import (
    analytics,
    campaigns,
    communications,
    certificates,
    clients,
    dashboard,
    feedback,
    messages,
    news,
    operations,
    products,
    referral_programs,
    security,
    system_settings,
    traffic,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(health.router)
router.include_router(app_feedback.router)

router.include_router(dashboard.router)
router.include_router(analytics.router)
router.include_router(operations.router)
router.include_router(clients.router)
router.include_router(messages.router)
router.include_router(news.router)
router.include_router(campaigns.router)
router.include_router(communications.router)
router.include_router(feedback.router)
router.include_router(products.router)
router.include_router(certificates.router)
router.include_router(referral_programs.router)
router.include_router(traffic.router)
router.include_router(security.router)
router.include_router(system_settings.router)
