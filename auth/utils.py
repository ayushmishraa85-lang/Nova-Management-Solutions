"""
Authentication Utilities
Validation helpers for email, password, and error formatting
"""

import re
from typing import Tuple


def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_strong: bool, error_message: str)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("At least 8 characters")
    
    if not re.search(r'[A-Z]', password):
        errors.append("At least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("At least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        errors.append("At least one digit")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append("At least one special character (!@#$%^&*)")
    
    if errors:
        message = "Password must include:\n- " + "\n- ".join(errors)
        return False, message
    
    return True, "✅ Strong password"


def format_error_message(error: str) -> str:
    """
    Format error messages for display.
    
    Args:
        error: Original error message
    
    Returns:
        Formatted error message
    """
    # Map database/technical errors to user-friendly messages
    error_map = {
        "duplicate key": "This email is already registered.",
        "connection refused": "Database connection error. Please try again.",
        "authentication failed": "Authentication failed. Please check your credentials.",
    }
    
    error_lower = error.lower()
    for key, friendly_message in error_map.items():
        if key in error_lower:
            return friendly_message
    
    return error if error else "An unexpected error occurred."


def sanitize_input(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not input_str:
        return ""
    
    # Remove leading/trailing whitespace
    sanitized = input_str.strip()
    
    # Truncate to max length
    sanitized = sanitized[:max_length]
    
    # Remove null bytes
    sanitized = sanitized.replace('\0', '')
    
    return sanitized
