from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from flask import Flask, current_app
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def _build_engine(url: str) -> Engine:
    normalized = _normalize_database_url(url)
    common: dict[str, object] = {"pool_pre_ping": True}

    if normalized.startswith("sqlite"):
        common.update(
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    elif ":6543/" in normalized:
        common.update(
            poolclass=NullPool,
            connect_args={"prepare_threshold": None},
        )
    else:
        common.update(pool_size=5, max_overflow=2, pool_recycle=1800)

    return create_engine(normalized, **common)


def init_db(app: Flask) -> None:
    database_url = app.config.get("DATABASE_URL", "")
    if not database_url:
        app.extensions["db_engine"] = None
        app.extensions["db_session_factory"] = None
        return

    engine = _build_engine(database_url)
    app.extensions["db_engine"] = engine
    app.extensions["db_session_factory"] = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


def get_engine() -> Engine | None:
    return current_app.extensions.get("db_engine")


@contextmanager
def session_scope() -> Iterator[Session]:
    factory: sessionmaker[Session] | None = current_app.extensions.get(
        "db_session_factory"
    )
    if factory is None:
        raise RuntimeError("DATABASE_URL is not configured.")

    with factory() as session:
        yield session


def database_ready() -> tuple[bool, str]:
    engine = get_engine()
    if engine is None:
        return False, "not_configured"
    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        return True, "up"
    except Exception:
        current_app.logger.exception("Database readiness check failed")
        return False, "down"
