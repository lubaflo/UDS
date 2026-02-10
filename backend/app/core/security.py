from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import parse_qsl

from jose import jwt

from app.core.config import settings


@dataclass(frozen=True)
class TelegramUser:
    tg_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]


class SecurityError(Exception):
    pass


def _build_telegram_secret_key(bot_token: str) -> bytes:
    # Per Telegram Web Apps docs: secret_key = HMAC_SHA256("WebAppData", bot_token)
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def verify_telegram_init_data(init_data: str, max_age_seconds: int = 60 * 60 * 24) -> TelegramUser:
    """
    Validates initData from Telegram WebApp.
    - Verifies hash
    - Verifies auth_date not too old
    """
    if not init_data or "hash=" not in init_data:
        raise SecurityError("initData is empty or missing hash")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise SecurityError("initData missing hash")

    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted(pairs.items(), key=lambda x: x[0])])

    secret_key = _build_telegram_secret_key(settings.TELEGRAM_BOT_TOKEN)
    computed_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise SecurityError("initData hash mismatch")

    auth_date_str = pairs.get("auth_date")
    if not auth_date_str:
        raise SecurityError("initData missing auth_date")

    try:
        auth_date = int(auth_date_str)
    except ValueError as e:
        raise SecurityError("initData auth_date invalid") from e

    now = int(time.time())
    if auth_date > now + 30:
        raise SecurityError("initData auth_date from future")
    if now - auth_date > max_age_seconds:
        raise SecurityError("initData expired")

    user_json = pairs.get("user")
    if not user_json:
        raise SecurityError("initData missing user")

    # user is JSON; parse safely without heavy deps
    # Telegram sends compact JSON, e.g. {"id":123,"first_name":"A","username":"u"}
    import json as _json  # local import

    try:
        user_obj = _json.loads(user_json)
    except Exception as e:
        raise SecurityError("initData user json invalid") from e

    tg_id = int(user_obj.get("id"))
    return TelegramUser(
        tg_id=tg_id,
        username=user_obj.get("username"),
        first_name=user_obj.get("first_name"),
        last_name=user_obj.get("last_name"),
    )


def issue_jwt(payload: dict[str, Any]) -> str:
    now = int(time.time())
    claims = {
        **payload,
        "iat": now,
        "exp": now + settings.JWT_TTL_SECONDS,
    }
    return jwt.encode(claims, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except Exception as e:
        raise SecurityError("Invalid token") from e