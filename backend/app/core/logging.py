from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import Request


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "ts": int(time.time() * 1000),
        }
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]


def request_log_extra(request: Request, **kwargs: Any) -> dict[str, Any]:
    client_host = request.client.host if request.client else None
    return {
        "request_id": getattr(request.state, "request_id", None),
        "path": request.url.path,
        "method": request.method,
        "client_ip": client_host,
        **kwargs,
    }