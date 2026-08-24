"""
database/connection.py — engine creation and health checks.

Reads DATABASE_URL from (in order): the environment, then Streamlit
secrets. Never hardcodes credentials. Provides one reusable, cached engine
per process instead of opening a new connection per query.

DATABASE_URL format:
    postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME

Local development (.env, not committed — see .gitignore):
    DATABASE_URL=postgresql+psycopg://novams:novams@localhost:5432/novams

Streamlit Cloud deployment (Settings → Secrets):
    DATABASE_URL = "postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME"

`localhost` / `127.0.0.1` / `::1` must never be used as the production
host — Streamlit Cloud cannot reach a database on the machine running the
app. Use a remotely hosted Postgres instance (Supabase, Neon, Render,
RDS, etc.) and put its connection string in DATABASE_URL.
"""

from __future__ import annotations

import os
from typing import Optional

try:
    import streamlit as st
except ImportError:  # pragma: no cover - module is also unit-testable
    st = None  # type: ignore

try:
    from dotenv import load_dotenv
    load_dotenv()  # no-op if no .env file is present; never overwrites real env vars
except ImportError:
    pass

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def get_database_url() -> Optional[str]:
    """
    Returns the configured DATABASE_URL, or None if not configured.
    Checks the environment first, then st.secrets — never logs or
    displays the value anywhere.
    """
    url = os.environ.get("DATABASE_URL")
    if url:
        return url.strip()
    if st is not None:
        try:
            url = st.secrets.get("DATABASE_URL")
            if url:
                return str(url).strip()
        except Exception:
            pass
    return None


def is_production_unsafe_host(database_url: str) -> bool:
    """True if the URL points at a loopback host — fine locally, never in production."""
    try:
        from urllib.parse import urlparse
        host = urlparse(database_url).hostname or ""
        return host.lower() in _LOCALHOST_HOSTS
    except Exception:
        return False


def _build_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,   # detects and replaces dropped connections automatically
        pool_size=5,
        max_overflow=5,
        pool_recycle=1800,
        future=True,
    )


if st is not None:
    @st.cache_resource(show_spinner=False)
    def _cached_engine(database_url: str) -> Engine:
        return _build_engine(database_url)
else:  # pragma: no cover - fallback for plain-Python unit tests
    _engine_singleton: dict[str, Engine] = {}

    def _cached_engine(database_url: str) -> Engine:
        if database_url not in _engine_singleton:
            _engine_singleton[database_url] = _build_engine(database_url)
        return _engine_singleton[database_url]


def get_engine() -> Optional[Engine]:
    """
    Returns a reusable, process-cached SQLAlchemy engine, or None if
    DATABASE_URL isn't configured. Never raises — connection problems only
    surface when a query actually runs, via check_health()/queries.py,
    each wrapped in try/except by the caller.
    """
    url = get_database_url()
    if not url:
        return None
    try:
        return _cached_engine(url)
    except Exception:
        return None


def check_health(engine: Optional[Engine] = None) -> dict:
    """
    Lightweight connectivity check. Returns a structured result instead of
    raising, so the UI can show a clear message rather than crash.
    """
    if engine is None:
        engine = get_engine()
    if engine is None:
        return dict(ok=False, configured=False, message="DATABASE_URL is not configured.")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return dict(ok=True, configured=True, message="Connected.")
    except Exception as e:
        return dict(ok=False, configured=True, message=f"Connection failed: {e}")
