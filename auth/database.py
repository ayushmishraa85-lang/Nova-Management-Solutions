"""
PostgreSQL Database Operations for Authentication
Handles user creation, retrieval, verification, and activity logging
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


def get_db_connection():
    """
    Get PostgreSQL connection from Streamlit secrets.
    Adapt this if your existing NovaMS uses a different connection method.
    
    Supports two patterns:
    1. DATABASE_URL = "postgresql://user:password@host:port/dbname"
    2. Individual credentials: PG_HOST, PG_USER, PG_PASSWORD, PG_DATABASE, PG_PORT
    """
    try:
        # Try Streamlit connection first (if already configured)
        if hasattr(st, "connection"):
            try:
                return st.connection("postgresql")
            except Exception:
                pass
        
        # Fall back to direct psycopg2 connection
        db_config = {
            "host": st.secrets.get("PG_HOST", "localhost"),
            "user": st.secrets.get("PG_USER", "postgres"),
            "password": st.secrets.get("PG_PASSWORD", ""),
            "database": st.secrets.get("PG_DATABASE", "novams"),
            "port": st.secrets.get("PG_PORT", 5432),
        }
        
        conn = psycopg2.connect(**db_config)
        return conn
    
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        st.error("❌ Database connection failed. Check secrets.toml configuration.")
        raise


def init_users_table():
    """
    Create users table if it doesn't exist.
    Call this once during app initialization.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
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
        """)
        
        # Create activity_log table for tracking user actions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action VARCHAR(255) NOT NULL,
                details TEXT,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indices for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_is_verified ON users(is_verified);
            CREATE INDEX IF NOT EXISTS idx_activity_log_user_id ON activity_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, role, is_verified)
            VALUES (%s, %s, %s, %s, FALSE)
            RETURNING id;
        """, (email, password_hash, name, role))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"✅ User created: {email} (ID: {user_id})")
        return True, f"Account created successfully. Please verify your email.", user_id
    
    except psycopg2.IntegrityError:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, "Email already registered. Please login or use another email.", None
    
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False, f"Error: {str(e)}", None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Retrieve user by email.
    
    Returns:
        Dict with user data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, email, password_hash, name, role, is_verified, created_at, last_login
            FROM users
            WHERE email = %s AND is_active = TRUE;
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return dict(user) if user else None
    
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Retrieve user by ID.
    
    Returns:
        Dict with user data or None if not found
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, email, password_hash, name, role, is_verified, created_at, last_login
            FROM users
            WHERE id = %s AND is_active = TRUE;
        """, (user_id,))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return dict(user) if user else None
    
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET is_verified = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Error verifying user: {e}")
        return False


def update_last_login(user_id: int) -> bool:
    """Update user's last login timestamp"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users
            SET last_login = CURRENT_TIMESTAMP
            WHERE id = %s;
        """, (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        logger.error(f"Error updating last login: {e}")
        return False


def log_activity(user_id: int, action: str, details: str = None, ip_address: str = None) -> bool:
    """
    Log user activity to database for audit trail.
    
    Args:
        user_id: User ID
        action: Action type (e.g., 'login', 'logout', 'data_export')
        details: Additional details about the action
        ip_address: User's IP address (optional)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO activity_log (user_id, action, details, ip_address)
            VALUES (%s, %s, %s, %s);
        """, (user_id, action, details, ip_address))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"📝 Activity logged: User {user_id} - {action}")
        return True
    
    except Exception as e:
        logger.error(f"Error logging activity: {e}")
        return False
