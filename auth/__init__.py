"""
NovaMS Authentication Package
Secure user authentication with PostgreSQL backend
"""

from .database import (
    init_users_table,
    create_user,
    get_user_by_email,
    verify_password,
    update_user_verified,
    log_activity,
    get_user_by_id,
    update_last_login,
)
from .hashing import hash_password, verify_password as verify_pwd
from .otp import generate_otp, verify_otp, send_otp_email, get_otp_status, clear_otp
from .session import (
    init_session_state,
    set_session_user,
    get_session_user,
    clear_session,
    is_authenticated,
    get_user_role,
    require_auth,
    require_admin,
    require_verified_email,
)
from .utils import is_valid_email, is_strong_password, format_error_message

__all__ = [
    "init_users_table",
    "create_user",
    "get_user_by_email",
    "verify_password",
    "update_user_verified",
    "log_activity",
    "get_user_by_id",
    "update_last_login",
    "hash_password",
    "verify_pwd",
    "generate_otp",
    "verify_otp",
    "send_otp_email",
    "get_otp_status",
    "clear_otp",
    "init_session_state",
    "set_session_user",
    "get_session_user",
    "clear_session",
    "is_authenticated",
    "get_user_role",
    "require_auth",
    "require_admin",
    "require_verified_email",
    "is_valid_email",
    "is_strong_password",
    "format_error_message",
]
