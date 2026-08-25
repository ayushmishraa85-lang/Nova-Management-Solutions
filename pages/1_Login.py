"""
NovaMS Login Page
User authentication and session management
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import (
    init_session_state,
    verify_password,
    set_session_user,
    update_last_login,
    log_activity,
    is_valid_email,
    format_error_message,
)
from auth.database import init_users_table

# Page configuration
st.set_page_config(
    page_title="Login - NovaMS",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Initialize session
init_session_state()

# Initialize database tables
init_users_table()

# If already logged in, redirect to dashboard
if st.session_state.is_authenticated:
    st.success("✅ You're already logged in!")
    st.info("👉 Go to the **Dashboard** page to view analytics.")
    st.stop()


def login_page():
    """Render login page UI"""
    
    # Header
    st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: 50px auto;
            }
            .login-header {
                text-align: center;
                margin-bottom: 40px;
            }
            .login-header h1 {
                font-size: 2.5em;
                color: #1D4DFF;
                margin-bottom: 10px;
            }
            .login-header p {
                color: #666;
                font-size: 1em;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="login-header">
                <h1>🚀 NovaMS</h1>
                <p>Nova Management Solutions</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        st.markdown("### 🔐 Sign In")
        
        email = st.text_input(
            "Email Address",
            placeholder="you@example.com",
            help="Enter your registered email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            help="Enter your password"
        )
        
        remember_me = st.checkbox("Remember me", value=False)
        
        submitted = st.form_submit_button(
            "🔓 Sign In",
            use_container_width=True,
            type="primary"
        )
    
    # Handle login
    if submitted:
        if not email or not password:
            st.error("❌ Please enter both email and password.")
            return
        
        if not is_valid_email(email):
            st.error("❌ Please enter a valid email address.")
            return
        
        # Verify credentials
        is_correct, user = verify_password(email, password)
        
        if not is_correct:
            st.error("❌ Invalid email or password.")
            log_activity(None, "failed_login_attempt", f"Email: {email}")
            return
        
        # Check if email verified
        if not user.get("is_verified"):
            st.warning("📧 Please verify your email before logging in.")
            st.info("Check your email for verification instructions. Not received? [Click here to resend OTP](#)")
            return
        
        # Update last login timestamp
        update_last_login(user["id"])
        
        # Set session
        set_session_user(user)
        
        # Log activity
        log_activity(user["id"], "login", "User logged in successfully")
        
        # Success
        st.success("✅ Login successful!")
        st.balloons()
        st.rerun()
    
    # Divider
    st.markdown("---")
    
    # Sign up link
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center;">
                <p>Don't have an account?</p>
                <a href="/Signup" target="_self" style="color: #1D4DFF; font-weight: bold; text-decoration: none;">
                    Create account →
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    # Footer info
    st.markdown("""
        ---
        <div style="text-align: center; color: #999; font-size: 0.85em; margin-top: 30px;">
            <p>🔒 Your data is encrypted and secure</p>
            <p style="margin-top: 10px;">
                <a href="#" style="color: #999; text-decoration: none; margin: 0 10px;">Privacy Policy</a> •
                <a href="#" style="color: #999; text-decoration: none; margin: 0 10px;">Terms</a>
            </p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    login_page()
