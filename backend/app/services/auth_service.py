from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TelegramUser, issue_jwt
from app.models import Salon, User


def _pick_or_create_default_salon(db: Session) -> Salon:
    salon = db.execute(select(Salon).limit(1)).scalar_one_or_none()
    if salon:
        return salon
    salon = Salon(name=settings.DEFAULT_SALON_NAME)
    db.add(salon)
    db.flush()
    return salon


def _auto_provision_user(db: Session, salon: Salon, tg_user: TelegramUser) -> User:
    user = db.execute(select(User).where(User.tg_id == tg_user.tg_id)).scalar_one_or_none()
    if user:
        if not user.is_active:
            user.is_active = True
        if not user.display_name:
            user.display_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip()
        return user

    admin_ids = {x.strip() for x in settings.ADMIN_TG_IDS.split(",") if x.strip()}
    role = "admin"
    if str(tg_user.tg_id) in admin_ids:
        role = "owner"

    user = User(
        salon_id=salon.id,
        tg_id=tg_user.tg_id,
        role=role,
        is_active=True,
        display_name=f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip(),
    )
    db.add(user)
    db.flush()
    return user


def login_with_telegram(db: Session, tg_user: TelegramUser) -> str:
    salon = _pick_or_create_default_salon(db)
    user = _auto_provision_user(db, salon, tg_user)

    now = int(time.time())
    token = issue_jwt(
        {
            "sub": str(user.id),
            "salon_id": salon.id,
            "role": user.role,
            "tg_id": user.tg_id,
            "ts": now,
        }
    )
    return token