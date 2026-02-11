from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.api.v1 import router as v1_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import ReminderRule, Salon, SystemSettings, TrafficChannel

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.CORS_ALLOW_ORIGINS.split(",") if x.strip()] or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        salon = db.execute(select(Salon).limit(1)).scalar_one_or_none()
        if salon is None:
            salon = Salon(
                name=settings.DEFAULT_SALON_NAME,
                moderation_status="in_review",
            )
            db.add(salon)
            db.flush()

        if salon.moderation_status is None:
            salon.moderation_status = "in_review"

        settings_row = db.execute(
            select(SystemSettings).where(SystemSettings.salon_id == salon.id)
        ).scalar_one_or_none()
        if settings_row is None:
            db.add(SystemSettings(salon_id=salon.id))

        reminder_count = db.execute(
            select(func.count()).where(ReminderRule.salon_id == salon.id)
        ).scalar_one()
        if not reminder_count:
            for offset in [60, 240, 1440, 10080]:
                db.add(ReminderRule(salon_id=salon.id, offset_minutes=offset, channel="app", is_enabled=True))

        defaults = [
            ("Web", "web", ""),
            ("UDS App", "uds_app", ""),
            ("Новые компании", "partner", ""),
            ("Размещения по CPA", "cpa", ""),
            ("Буферные клиенты", "buffer", ""),
        ]
        existing = {x.name for x in db.execute(select(TrafficChannel).where(TrafficChannel.salon_id == salon.id)).scalars().all()}
        now = int(time.time())
        for name, channel_type, promo_code in defaults:
            if name not in existing:
                db.add(
                    TrafficChannel(
                        salon_id=salon.id,
                        name=name,
                        channel_type=channel_type,
                        promo_code=promo_code,
                        created_at=now,
                    )
                )
        db.commit()


app.include_router(v1_router)


@app.get("/")
async def root() -> dict:
    return {"service": settings.APP_NAME, "version": settings.APP_VERSION, "status": "ok"}
