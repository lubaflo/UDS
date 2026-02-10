from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.security import SecurityError, decode_jwt
from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@dataclass(frozen=True)
class AuthCtx:
    user_id: int
    salon_id: int
    role: str
    tg_id: int


def get_auth_ctx(authorization: str = Header(default="")) -> AuthCtx:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_jwt(token)
    except SecurityError:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        return AuthCtx(
            user_id=int(claims["sub"]),
            salon_id=int(claims["salon_id"]),
            role=str(claims["role"]),
            tg_id=int(claims["tg_id"]),
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token claims")


def require_roles(*roles: str):
    def _dep(ctx: AuthCtx = Depends(get_auth_ctx)) -> AuthCtx:
        if ctx.role not in roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return ctx

    return _dep