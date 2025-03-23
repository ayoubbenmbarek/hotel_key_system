import re
import requests
from typing import List, Optional, Dict, Any, Tuple
from twilio.rest import Client
import logging

from app.config import settings


# Configure logging
logger = logging.getLogger(__name__)

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    Basic validation - you may want to use a library like phonenumbers for more accurate validation
    """
    # Remove spaces, dashes, and parentheses
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Basic validation: Check if it's numeric and reasonable length
    if clean_phone.startswith('+'):
        # International format
        return clean_phone[1:].isdigit() and 10 <= len(clean_phone) <= 15
    else:
        # National format
        return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15


def send_sms(to_number: str, message: str) -> Tuple[bool, str]:
    """
    Send SMS using a third-party service
    """
    try:
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            print(f"Missing Twilio credentials: SID={settings.TWILIO_ACCOUNT_SID}, Token={'present' if settings.TWILIO_AUTH_TOKEN else 'missing'}")
            return False, "Twilio credentials not configured"
        try:
            print(f"Attempting to send SMS to {to_number} using Twilio number {settings.TWILIO_PHONE_NUMBER}")            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            
            return True, f"SMS sent successfully. SID: {message.sid}"
        
        except ImportError:
            # If Twilio isn't installed, try a generic HTTP API approach
            try:
                # This is a placeholder - replace with your actual SMS provider's API
                response = requests.post(
                    settings.SMS_API_URL,
                    json={
                        "to": to_number,
                        "message": message,
                        "api_key": settings.SMS_API_KEY
                    },
                    timeout=10  # Add timeout of 10 seconds
                )
                
                if response.status_code == 200:
                    return True, "SMS sent successfully"
                else:
                    return False, f"SMS API error: {response.text}"
                    
            except Exception as e:
                return False, f"SMS sending failed: {str(e)}"
    except Exception as e:
        print(f"SMS sending failed with exception: {str(e)}")
        return False, f"SMS sending failed: {str(e)}"


# def send_sms(to_number: str, message: str) -> Tuple[bool, str]:
#     """Send SMS using TextBelt"""
#     try:
#         logger.info(f"Attempting to send SMS to {to_number} via TextBelt")
        
#         response = requests.post('https://textbelt.com/text', {
#             'phone': to_number,
#             'message': message,
#             'key': 'textbelt',  # Free tier: 1 SMS per day with this key
#         }, timeout=10)  # Add timeout of 10 seconds
        
#         result = response.json()
#         if result.get('success'):
#             logger.info(f"TextBelt SMS sent successfully: {result}")
#             return True, f"SMS sent successfully. TextID: {result.get('textId')}"
#         else:
#             logger.error(f"TextBelt SMS failed: {result}")
#             return False, f"SMS sending failed: {result.get('error')}"
            
#     except Exception as e:
#         logger.error(f"SMS sending exception: {str(e)}")
#         logger.exception("Detailed SMS error:")
#         return False, f"SMS sending failed: {str(e)}"