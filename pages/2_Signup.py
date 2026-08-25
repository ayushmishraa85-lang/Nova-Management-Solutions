"""
NovaMS Signup Page
User registration and email verification
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import (
    init_session_state,
    create_user,
    hash_password,
    is_valid_email,
    is_strong_password,
    generate_otp,
    verify_otp,
    send_otp_email,
    get_otp_status,
    log_activity,
)
from auth.database import init_users_table, update_user_verified

# Page configuration
st.set_page_config(
    page_title="Signup - NovaMS",
    page_icon="📝",
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


def signup_page():
    """Render signup page UI"""
    
    # Header
    st.markdown("""
        <style>
            .signup-container {
                max-width: 400px;
                margin: 30px auto;
            }
            .signup-header {
                text-align: center;
                margin-bottom: 40px;
            }
            .signup-header h1 {
                font-size: 2.5em;
                color: #1D4DFF;
                margin-bottom: 10px;
            }
            .signup-header p {
                color: #666;
                font-size: 1em;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="signup-header">
                <h1>🚀 NovaMS</h1>
                <p>Create Your Account</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Signup form
    with st.form("signup_form"):
        st.markdown("### 📝 Sign Up")
        
        name = st.text_input(
            "Full Name",
            placeholder="John Doe",
            help="Your full name"
        )
        
        email = st.text_input(
            "Email Address",
            placeholder="you@example.com",
            help="Use a real email for verification"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="••••••••",
            help="At least 8 characters with uppercase, lowercase, digit, and special character"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="••••••••"
        )
        
        agree_terms = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            value=False
        )
        
        submitted = st.form_submit_button(
            "✍️ Create Account",
            use_container_width=True,
            type="primary"
        )
    
    # Handle signup
    if submitted:
        # Validation
        if not all([name, email, password, confirm_password]):
            st.error("❌ Please fill in all fields.")
            return
        
        if not is_valid_email(email):
            st.error("❌ Please enter a valid email address.")
            return
        
        if password != confirm_password:
            st.error("❌ Passwords do not match.")
            return
        
        is_strong, msg = is_strong_password(password)
        if not is_strong:
            st.error(f"❌ Password is not strong enough.\n\n{msg}")
            return
        
        if not agree_terms:
            st.error("❌ Please agree to the Terms of Service.")
            return
        
        # Hash password
        try:
            password_hash = hash_password(password)
        except ValueError as e:
            st.error(f"❌ {str(e)}")
            return
        
        # Create user
        success, message, user_id = create_user(email, password_hash, name, role="user")
        
        if not success:
            st.error(f"❌ {message}")
            return
        
        # Generate OTP
        otp_code = generate_otp(email, length=6, expiry_minutes=10)
        
        # Send OTP (dev mode shows it in app)
        send_otp_email(email, otp_code, dev_mode=True)
        
        # Store signup info in session
        st.session_state.signup_user_id = user_id
        st.session_state.signup_email = email
        st.session_state.show_otp_verification = True
        
        st.success("✅ Account created! Please verify your email.")
        st.info(f"📧 OTP sent to {email}")
        st.rerun()
    
    # OTP Verification
    if st.session_state.get("show_otp_verification"):
        st.markdown("---")
        st.markdown("### 📧 Verify Email")
        
        email = st.session_state.signup_email
        
        # Show OTP for development
        otp_status = get_otp_status(email)
        if otp_status:
            with st.expander("🔍 [DEV] Show OTP Code", expanded=False):
                st.code(f"OTP Code: {otp_status['code']}", language="text")
                st.caption(f"⏱️ Expires in: {int(otp_status['expires_in_seconds'])} seconds")
                st.caption(f"⚠️ Attempts remaining: {otp_status['attempts_remaining']}")
        
        with st.form("otp_verification_form"):
            otp_input = st.text_input(
                "Enter OTP",
                placeholder="000000",
                help="6-digit code from your email"
            )
            
            verify_submitted = st.form_submit_button(
                "✅ Verify Email",
                use_container_width=True,
                type="primary"
            )
        
        if verify_submitted:
            if not otp_input:
                st.error("❌ Please enter the OTP.")
                return
            
            is_valid, otp_message = verify_otp(email, otp_input)
            
            if is_valid:
                # Mark user as verified
                update_user_verified(st.session_state.signup_user_id)
                
                # Log activity
                log_activity(
                    st.session_state.signup_user_id,
                    "email_verified",
                    f"User verified email: {email}"
                )
                
                st.success("✅ Email verified successfully!")
                st.success("🎉 Your account is ready to use!")
                st.info("👉 Go to the **Login** page to sign in.")
                
                # Clear signup session
                st.session_state.show_otp_verification = False
                st.session_state.signup_user_id = None
                st.session_state.signup_email = None
                st.rerun()
            else:
                st.error(otp_message)
        
        # Resend OTP
        if st.button("🔄 Resend OTP"):
            new_otp = generate_otp(email, length=6, expiry_minutes=10)
            send_otp_email(email, new_otp, dev_mode=True)
            st.success("✅ New OTP sent!")
            st.rerun()
    
    # Divider
    st.markdown("---")
    
    # Login link
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center;">
                <p>Already have an account?</p>
                <a href="/Login" target="_self" style="color: #1D4DFF; font-weight: bold; text-decoration: none;">
                    Sign in →
                </a>
            </div>
        """, unsafe_allow_html=True)
    
    # Footer info
    st.markdown("""
        ---
        <div style="text-align: center; color: #999; font-size: 0.85em; margin-top: 30px;">
            <p>🔒 Your data is encrypted and secure</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    signup_page()
