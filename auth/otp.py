"""
OTP (One-Time Password) Module
Generates and verifies OTPs for email verification
Dev-first approach: shows OTP in-app, ready for email integration
"""

import random
import string
import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional
import streamlit as st

logger = logging.getLogger(__name__)


# In-memory OTP storage (for development)
# In production, store in Redis or database with TTL
OTP_STORAGE = {}  # Format: {email: {"code": "123456", "expires_at": datetime, "attempts": 0}}


def generate_otp(email: str, length: int = 6, expiry_minutes: int = 10) -> str:
    """
    Generate a random OTP for email verification.
    
    Args:
        email: User email
        length: OTP length (default: 6 digits)
        expiry_minutes: OTP expiry time in minutes (default: 10)
    
    Returns:
        OTP code (string of digits)
    """
    try:
        # Generate random 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=length))
        
        # Store in memory with expiry
        OTP_STORAGE[email] = {
            "code": otp_code,
            "expires_at": datetime.now() + timedelta(minutes=expiry_minutes),
            "attempts": 0,
            "created_at": datetime.now()
        }
        
        logger.info(f"✅ OTP generated for {email}")
        return otp_code
    
    except Exception as e:
        logger.error(f"Error generating OTP: {e}")
        raise


def verify_otp(email: str, otp_code: str, max_attempts: int = 5) -> Tuple[bool, str]:
    """
    Verify OTP code for email.
    
    Args:
        email: User email
        otp_code: OTP code to verify
        max_attempts: Maximum verification attempts allowed
    
    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    try:
        # Check if OTP exists
        if email not in OTP_STORAGE:
            return False, "❌ No OTP found. Request a new one."
        
        otp_data = OTP_STORAGE[email]
        
        # Check if OTP expired
        if datetime.now() > otp_data["expires_at"]:
            del OTP_STORAGE[email]
            return False, "❌ OTP expired. Request a new one."
        
        # Check attempts
        if otp_data["attempts"] >= max_attempts:
            del OTP_STORAGE[email]
            return False, f"❌ Too many failed attempts. Request a new OTP."
        
        # Verify code
        if otp_data["code"] == otp_code:
            del OTP_STORAGE[email]
            logger.info(f"✅ OTP verified for {email}")
            return True, "✅ Email verified successfully!"
        
        # Increment failed attempts
        otp_data["attempts"] += 1
        remaining = max_attempts - otp_data["attempts"]
        
        return False, f"❌ Incorrect OTP. {remaining} attempts remaining."
    
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        return False, "❌ Error verifying OTP. Please try again."


def send_otp_email(email: str, otp_code: str, dev_mode: bool = True) -> bool:
    """
    Send OTP via email.
    
    DEVELOPMENT MODE: Shows OTP in Streamlit UI
    PRODUCTION MODE: Use Resend, SendGrid, or SMTP
    
    Args:
        email: Recipient email
        otp_code: OTP code to send
        dev_mode: If True, displays OTP in app (for testing)
    
    Returns:
        True if email sent successfully
    """
    try:
        if dev_mode:
            # Development mode: Display OTP in Streamlit UI
            logger.info(f"📧 [DEV MODE] OTP for {email}: {otp_code}")
            return True
        
        # Production mode: Implement Resend/SendGrid/SMTP here
        # Example with Resend (requires API key in secrets):
        """
        from resend import Resend
        
        client = Resend(api_key=st.secrets.get("RESEND_API_KEY"))
        
        email_data = {
            "from": "noreply@novams.com",
            "to": email,
            "subject": "NovaMS Email Verification",
            "html": f'''
                <h2>Verify Your Email</h2>
                <p>Your OTP is: <strong>{otp_code}</strong></p>
                <p>This OTP will expire in 10 minutes.</p>
            '''
        }
        
        response = client.emails.send(email_data)
        logger.info(f"✅ Email sent to {email}: {response}")
        return True
        """
        
        # Fallback: Log error
        logger.error("Email sending not configured for production mode")
        return False
    
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        return False


def get_otp_status(email: str) -> Optional[dict]:
    """Get OTP status for display (for testing)"""
    if email in OTP_STORAGE:
        data = OTP_STORAGE[email]
        return {
            "code": data["code"],
            "expires_in_seconds": (data["expires_at"] - datetime.now()).total_seconds(),
            "attempts_remaining": 5 - data["attempts"]
        }
    return None


def clear_otp(email: str) -> bool:
    """Clear OTP for email"""
    try:
        if email in OTP_STORAGE:
            del OTP_STORAGE[email]
        return True
    except Exception as e:
        logger.error(f"Error clearing OTP: {e}")
        return False
