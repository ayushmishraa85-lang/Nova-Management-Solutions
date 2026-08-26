"""
NovaMS User Profile Page
View and manage user account settings
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import (
    init_session_state,
    get_session_user,
    require_auth,
    log_activity,
)
from auth.database import get_engine
from auth.hashing import hash_password, verify_password as verify_pwd
from sqlalchemy import text

# Page configuration
st.set_page_config(
    page_title="Profile - NovaMS",
    page_icon="👤",
    layout="wide",
)

# Initialize session
init_session_state()

# Require authentication
require_auth("the profile page")


def update_user_profile(user_id: int, name: str = None, password: str = None) -> bool:
    """Update user profile in database"""
    engine = get_engine()
    if engine is None:
        st.error("Database not configured.")
        return False

    try:
        with engine.begin() as conn:
            if name:
                conn.execute(
                    text("UPDATE users SET name = :name, updated_at = CURRENT_TIMESTAMP WHERE id = :user_id;"),
                    dict(name=name, user_id=user_id),
                )
            if password:
                password_hash = hash_password(password)
                conn.execute(
                    text("UPDATE users SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP WHERE id = :user_id;"),
                    dict(password_hash=password_hash, user_id=user_id),
                )
        return True

    except Exception as e:
        st.error(f"Error updating profile: {e}")
        return False


def profile_page():
    """Render user profile page"""
    
    user = get_session_user()
    
    st.markdown("# 👤 My Profile")
    st.markdown("---")
    
    # User Info Section
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Account Info")
        st.metric("User ID", user["id"])
        st.metric("Role", user["role"].upper(), delta="", delta_color="off")
        st.metric(
            "Email Verified",
            "✅ Yes" if user.get("is_verified") else "❌ No"
        )
    
    with col2:
        st.markdown("### Account Details")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.write(f"**Email:** {user.get('email')}")
            st.write(f"**Name:** {user.get('name')}")
        
        with col_b:
            st.write(f"**Created:** {user.get('created_at')}")
            if user.get("last_login"):
                st.write(f"**Last Login:** {user.get('last_login')}")
    
    st.markdown("---")
    
    # Edit Profile Section
    st.markdown("### ✏️ Edit Profile")
    
    with st.form("edit_profile_form"):
        new_name = st.text_input(
            "Full Name",
            value=user.get("name", ""),
            help="Update your full name"
        )
        
        submitted = st.form_submit_button(
            "💾 Save Changes",
            use_container_width=True,
            type="primary"
        )
    
    if submitted:
        if new_name and new_name != user.get("name"):
            if update_user_profile(user["id"], name=new_name):
                # Update session
                user["name"] = new_name
                st.session_state.auth_user = user
                
                log_activity(user["id"], "profile_updated", f"Updated name to: {new_name}")
                
                st.success("✅ Profile updated successfully!")
                st.rerun()
            else:
                st.error("Failed to update profile.")
        elif not new_name:
            st.error("Name cannot be empty.")
    
    st.markdown("---")
    
    # Change Password Section
    st.markdown("### 🔑 Change Password")
    
    with st.form("change_password_form"):
        current_password = st.text_input(
            "Current Password",
            type="password",
            help="Enter your current password to verify"
        )
        
        new_password = st.text_input(
            "New Password",
            type="password",
            help="At least 8 characters with uppercase, lowercase, digit, and special character"
        )
        
        confirm_new_password = st.text_input(
            "Confirm New Password",
            type="password"
        )
        
        password_submitted = st.form_submit_button(
            "🔐 Change Password",
            use_container_width=True,
            type="primary"
        )
    
    if password_submitted:
        if not current_password or not new_password or not confirm_new_password:
            st.error("❌ Please fill in all password fields.")
            return
        
        # Verify current password
        if not verify_pwd(current_password, user.get("password_hash")):
            st.error("❌ Current password is incorrect.")
            return
        
        if new_password != confirm_new_password:
            st.error("❌ New passwords do not match.")
            return
        
        if len(new_password) < 8:
            st.error("❌ New password must be at least 8 characters.")
            return
        
        # Update password
        if update_user_profile(user["id"], password=new_password):
            log_activity(user["id"], "password_changed", "User changed password")
            
            st.success("✅ Password changed successfully!")
            st.info("🔐 Please log in again with your new password.")
            
            # Clear session after password change
            import time
            time.sleep(2)
            st.switch_page("pages/1_Login.py")
        else:
            st.error("Failed to change password.")
    
    st.markdown("---")
    
    # Security Section
    st.markdown("### 🛡️ Security")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
            ✅ **Your account is secure**
            - Passwords are hashed with bcrypt
            - Session tokens are managed securely
            - All data is encrypted in transit (HTTPS)
        """)
    
    with col2:
        st.warning("""
            ⚠️ **Security Tips**
            - Don't share your password
            - Log out on shared devices
            - Change password regularly
            - Keep your email updated
        """)
    
    st.markdown("---")
    
    # Danger Zone
    with st.expander("⚠️ Danger Zone", expanded=False):
        st.markdown("### 🗑️ Delete Account")
        
        st.error("""
            **Warning:** Deleting your account is permanent and cannot be undone.
            All your data will be permanently removed.
        """)
        
        if st.button("🗑️ Delete My Account", type="secondary"):
            st.warning("This feature is coming soon. Contact support to delete your account.")
    
    # Logout button (floating at bottom)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("👋 Logout", use_container_width=True, type="secondary"):
            st.switch_page("pages/3_Logout.py")


if __name__ == "__main__":
    profile_page()
