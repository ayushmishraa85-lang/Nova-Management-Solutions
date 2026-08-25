"""
NovaMS Logout Page
Session termination and user logout handling
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import (
    init_session_state,
    clear_session,
    get_session_user,
    log_activity,
    require_auth,
)

# Page configuration
st.set_page_config(
    page_title="Logout - NovaMS",
    page_icon="👋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Initialize session
init_session_state()

# Require authentication
require_auth("the logout page")


def logout_page():
    """Render logout confirmation"""
    
    user = get_session_user()
    
    st.markdown("""
        <style>
            .logout-container {
                text-align: center;
                margin-top: 50px;
            }
            .logout-container h1 {
                color: #1D4DFF;
                font-size: 2em;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="logout-container">
            <h1>👋 Goodbye, {name}!</h1>
        </div>
    """.format(name=user.get("name", "User")), unsafe_allow_html=True)
    
    # Logout confirmation
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("### Are you sure you want to logout?")
        
        col_yes, col_no = st.columns(2)
        
        with col_yes:
            if st.button("✅ Yes, Logout", use_container_width=True, type="primary"):
                # Log logout activity
                log_activity(
                    user["id"],
                    "logout",
                    f"User {user.get('email')} logged out"
                )
                
                # Clear session
                clear_session()
                
                st.success("✅ You have been logged out successfully!")
                st.info("👉 Redirecting to login page...")
                
                # Redirect to login
                st.switch_page("pages/1_Login.py")
        
        with col_no:
            if st.button("❌ Cancel", use_container_width=True):
                st.info("👉 Go to Dashboard to continue browsing.")
    
    # Info
    st.markdown("---")
    st.info("""
        💡 **Note:** Your session will be automatically cleared after logout.
        You can log back in anytime with your credentials.
    """)


if __name__ == "__main__":
    logout_page()
