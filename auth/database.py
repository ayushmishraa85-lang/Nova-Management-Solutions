"""
PostgreSQL Database Operations for Authentication
Handles user creation, retrieval, verification, and activity logging.

Uses SQLAlchemy + psycopg (v3) reading DATABASE_URL from Streamlit secrets —
the exact same pattern already used by NovaMS's PostgreSQL Sales Warehouse
(database/connection.py), so this reuses one connection convention across
the whole app instead of introducing a second (psycopg2-based) one.
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None


def _get_database_url() -> Optional[str]:
    """Reads DATABASE_URL from Streamlit secrets (Cloud) or environment (local)."""
    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass
    import os
    return os.environ.get("DATABASE_URL")


def get_engine() -> Optional[Engine]:
    """
    Returns a cached SQLAlchemy engine built from DATABASE_URL.
    Returns None if DATABASE_URL isn't configured — every caller must handle
    that case rather than crash, so the rest of the app keeps working.
    """
    global _engine
    if _engine is not None:
        return _engine

    url = _get_database_url()
    if not url:
        logger.error("DATABASE_URL not found in secrets or environment")
        return None

    try:
        _engine = create_engine(url, pool_pre_ping=True)
        return _engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        return None


def get_db_connection():
    """
    Legacy-named helper kept for compatibility with earlier auth module
    code — returns the SQLAlchemy engine (not a raw DBAPI connection).
    Every function below uses `with engine.connect() as conn:` / `engine.begin()`,
    which works the same way whether the engine came from here or was passed
    in directly.
    """
    return get_engine()


def init_users_table():
    """
    Create users table if it doesn't exist.
    Call this once during app initialization. Safe to call every run
    (CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS).
    """
    engine = get_engine()
    if engine is None:
        logger.error("Cannot initialize tables — no database engine available")
        return False

    try:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'user',
                    is_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    action VARCHAR(255) NOT NULL,
                    details TEXT,
                    ip_address VARCHAR(45),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_log_user_id ON activity_log(user_id);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);"))

        logger.info("✅ Users and activity_log tables initialized")
        return True

    except Exception as e:
        logger.error(f"Error initializing tables: {e}")
        return False


def create_user(email: str, password_hash: str, name: str, role: str = "user") -> Tuple[bool, str, Optional[int]]:
    """
    Create a new user in the database.

    Args:
        email: User email (must be unique)
        password_hash: Bcrypt hashed password
        name: User full name
        role: User role (default: 'user', can be 'admin')

    Returns:
        Tuple of (success: bool, message: str, user_id: Optional[int])
    """
    engine = get_engine()
    if engine is None:
        return False, "Database not configured. Check DATABASE_URL in secrets.", None

    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO users (email, password_hash, name, role, is_verified)
                    VALUES (:email, :password_hash, :name, :role, FALSE)
                    RETURNING id;
                """),
                dict(email=email, password_hash=password_hash, name=name, role=role),
            )
            user_id = result.scalar_one()

        logger.info(f"✅ User created: {email} (ID: {user_id})")
        return True, "Account created successfully. Please verify your email.", user_id

    except Exception as e:
        # SQLAlchemy wraps the underlying driver's unique-violation error;
        # checking the message text works across psycopg2/psycopg (v3) alike.
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return False, "Email already registered. Please login or use another email.", None
        logger.error(f"Error creating user: {e}")
        return False, f"Error: {str(e)}", None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Retrieve user by email.

    Returns:
        Dict with user data or None if not found
    """
    engine = get_engine()
    if engine is None:
        return None

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, email, password_hash, name, role, is_verified, created_at, last_login
                    FROM users
                    WHERE email = :email AND is_active = TRUE;
                """),
                dict(email=email),
            )
            row = result.mappings().first()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Retrieve user by ID.

    Returns:
        Dict with user data or None if not found
    """
    engine = get_engine()
    if engine is None:
        return None

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, email, password_hash, name, role, is_verified, created_at, last_login
                    FROM users
                    WHERE id = :user_id AND is_active = TRUE;
                """),
                dict(user_id=user_id),
            )
            row = result.mappings().first()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return None


def verify_password(email: str, password: str) -> Tuple[bool, Optional[Dict]]:
    """
    Verify user password during login.

    Returns:
        Tuple of (password_correct: bool, user_dict: Optional[Dict])
    """
    from .hashing import verify_password as verify_pwd

    user = get_user_by_email(email)
    if not user:
        return False, None

    if not verify_pwd(password, user["password_hash"]):
        return False, None

    return True, user


def update_user_verified(user_id: int) -> bool:
    """Mark user as email verified"""
    engine = get_engine()
    if engine is None:
        return False

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE users
                    SET is_verified = TRUE, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :user_id;
                """),
                dict(user_id=user_id),
            )
        return True

    except Exception as e:
        logger.error(f"Error verifying user: {e}")
        return False


def update_last_login(user_id: int) -> bool:
    """Update user's last login timestamp"""
    engine = get_engine()
    if engine is None:
        return False

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = :user_id;
                """),
                dict(user_id=user_id),
            )
        return True

    except Exception as e:
        logger.error(f"Error updating last login: {e}")
        return False


def log_activity(user_id: Optional[int], action: str, details: str = None, ip_address: str = None) -> bool:
    """
    Log user activity to database for audit trail.

    Args:
        user_id: User ID (can be None for pre-auth events like failed login attempts —
                 in that case this is skipped rather than violating the FK constraint)
        action: Action type (e.g., 'login', 'logout', 'data_export')
        details: Additional details about the action
        ip_address: User's IP address (optional)
    """
    if user_id is None:
        # activity_log.user_id is NOT NULL with a FK to users — there's no
        # user row to attach an anonymous event to, so just log it locally
        # instead of trying (and failing) to write to the table.
        logger.info(f"📝 [unattributed] {action}: {details}")
        return True

    engine = get_engine()
    if engine is None:
        return False

    try:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO activity_log (user_id, action, details, ip_address)
                    VALUES (:user_id, :action, :details, :ip_address);
                """),
                dict(user_id=user_id, action=action, details=details, ip_address=ip_address),
            )
        logger.info(f"📝 Activity logged: User {user_id} - {action}")
        return True

    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return False
