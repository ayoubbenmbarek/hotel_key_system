# backend/app/utils/validators.py
import re
from datetime import datetime, timedelta, timezone
from typing import Optional


def validate_phone_number(phone_number: str) -> bool:
    """
    Validate phone number format:
    - At least 10 digits
    - May contain spaces, dashes, parentheses
    """
    if not phone_number:
        return False
    
    # Remove non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Check length
    return len(digits_only) >= 10


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength:
    - At least 8 characters
    - Contains at least one digit
    - Contains at least one lowercase letter
    - Contains at least one uppercase letter
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    return True, None


def validate_email(email: str) -> bool:
    """
    Validate email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_reservation_dates(check_in: datetime, check_out: datetime) -> tuple[bool, Optional[str]]:
    """
    Validate reservation dates:
    - Check-out must be after check-in
    - Check-in cannot be in the past
    - Reservation cannot be more than 30 days
    """
    now = datetime.now(timezone.utc)
    
    if check_in < now:
        return False, "Check-in date cannot be in the past"
    
    if check_out <= check_in:
        return False, "Check-out date must be after check-in date"
    
    duration = check_out - check_in
    if duration > timedelta(days=30):
        return False, "Reservation cannot be more than 30 days"
    
    return True, None


def format_confirmation_code(code: str) -> str:
    """Format confirmation code for display"""
    if not code:
        return ""

    code = code.upper()
    if len(code) >= 3 and code.startswith("RES"):
        # Format as RES-XXXXX
        return f"{code[:3]}-{code[3:]}"

    return code
