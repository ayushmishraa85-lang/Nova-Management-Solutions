"""
Password Hashing Module
Uses bcrypt for secure password storage
"""

import bcrypt
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password (str)
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)  # 12 rounds = ~0.3 seconds per hash
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False
