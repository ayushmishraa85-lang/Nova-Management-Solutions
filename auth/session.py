"""
Session Management Module
Handles user session state via st.session_state
"""

import streamlit as st
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def init_session_state():
    """
    Initialize session state variables for authentication.
    Call this at the start of streamlit_app.py
    """
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    
    if "auth_message" not in st.session_state:
        st.session_state.auth_message = None
    
    if "show_signup_form" not in st.session_state:
        st.session_state.show_signup_form = False
    
    logger.debug("✅ Session state initialized")


def set_session_user(user_data: Dict):
    """
    Set authenticated user in session.
    
    Args:
        user_data: Dict with user info (id, email, name, role, is_verified, etc.)
    """
    try:
        st.session_state.auth_user = user_data
        st.session_state.is_authenticated = True
        st.session_state.user_role = user_data.get("role", "user")
        
        logger.info(f"✅ User session set: {user_data.get('email')}")
        return True
    
    except Exception as e:
        logger.error(f"Error setting session user: {e}")
        return False


def get_session_user() -> Optional[Dict]:
    """
    Get current authenticated user from session.
    
    Returns:
        User dict or None if not authenticated
    """
    return st.session_state.auth_user if st.session_state.is_authenticated else None


def is_authenticated() -> bool:
    """Check if user is currently authenticated"""
    return st.session_state.is_authenticated


def get_user_role() -> Optional[str]:
    """Get current user's role (admin, user, etc.)"""
    return st.session_state.user_role


def clear_session():
    """Clear user session (logout)"""
    try:
        st.session_state.auth_user = None
        st.session_state.is_authenticated = False
        st.session_state.user_role = None
        st.session_state.auth_message = None
        st.session_state.show_signup_form = False
        
        logger.info("✅ Session cleared (user logged out)")
        return True
    
    except Exception as e:
        logger.error(f"Error clearing session: {e}")
        return False


def require_auth(page_name: str = "this page"):
    """
    Require authentication to access a page.
    Call this at the start of protected pages.
    
    Args:
        page_name: Name of the page (for user-facing messages)
    """
    if not is_authenticated():
        st.warning(f"🔒 You must be logged in to access {page_name}.")
        st.info("👉 Please go to the **Login** page to authenticate.")
        st.stop()


def require_admin(page_name: str = "this page"):
    """
    Require admin role to access a page.
    
    Args:
        page_name: Name of the page
    """
    if not is_authenticated():
        st.warning(f"🔒 You must be logged in to access {page_name}.")
        st.stop()
    
    if get_user_role() != "admin":
        st.error(f"🚫 Admin access required to access {page_name}.")
        st.stop()


def require_verified_email(page_name: str = "this page"):
    """
    Require verified email to access a page.
    
    Args:
        page_name: Name of the page
    """
    if not is_authenticated():
        st.warning(f"🔒 You must be logged in to access {page_name}.")
        st.stop()
    
    user = get_session_user()
    if not user.get("is_verified"):
        st.warning(f"📧 Please verify your email to access {page_name}.")
        st.info("Check your email for verification instructions.")
        st.stop()
