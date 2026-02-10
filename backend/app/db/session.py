from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    # Works only for sqlite
    try:
        cursor = dbapi_connection.cursor()
        if settings.SQLITE_WAL:
            cursor.execute("PRAGMA journal_mode=WAL;")
        if settings.SQLITE_SYNCHRONOUS_NORMAL:
            cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()
    except Exception:
        # Do not crash on non-sqlite or restricted env
        pass


def db_healthcheck() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False