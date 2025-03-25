# wallet_push_service.py
import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
import jwt
from app.db.session import SessionLocal
import time
from datetime import datetime, timezone
import http.client
import uuid
import httpx

from app.config import settings
from app.db.session import get_db
from app.models.device import DeviceRegistration
from app.models.digital_key import DigitalKey
from app.models.key_event import KeyEvent

logger = logging.getLogger(__name__)

device_registrations = {}

# TODO: try to load env for production=True from .env
SERVER = "api.push.apple.com" if settings.PRODUCTION else "api.development.push.apple.com"
logger.info(f"Using APNs server: {SERVER}")
# CONN = http.client.HTTPSConnection(SERVER)


def send_push_notifications(pass_type_id, serial_number):
    """Send push notifications to all devices registered for a pass"""
    try:
        # Get registered devices for this pass
        key = f"{pass_type_id}:{serial_number}"
        if key not in device_registrations:
            logger.info(f"No registered devices for {key}")
            return
        
        # In production, you would use the Apple Push Notification Service (APNS)
        # For local testing, just log the notifications
        for reg in device_registrations[key]:
            logger.info(f"Would send push notification to device {reg['device_id']} with token {reg['push_token']}")
            
        logger.info(f"Push notifications sent for {key}")
        
    except Exception as e:
        logger.error(f"Error sending push notifications: {str(e)}")

# def send_push_notifications_production(pass_type_id, serial_number):
#     """Send push notifications to all devices registered for a pass (production)"""
#     try:
#         key = f"{pass_type_id}:{serial_number}"
#         if key not in device_registrations:
#             return
        
#         # Load your APNS authentication key
#         with open(settings.APPLE_PUSH_PRIVATE_KEY_PATH, 'r') as key_file:
#             auth_key = key_file.read()
        
#         # Create a JWT token for APNS authentication
#         token = jwt.encode(
#             {
#                 'iss': settings.APPLE_TEAM_ID,
#                 'iat': time.time()
#             },
#             auth_key,
#             algorithm='ES256',
#             headers={
#                 'kid': settings.APPLE_PUSH_KEY_ID
#             }
#         )
        
#         # Set up APNS connection
#         conn = http.client.HTTPSConnection(SERVER)
        
#         headers = {
#             "authorization": f"bearer {token}",
#             "apns-topic": f"pass.{pass_type_id}",
#             "apns-push-type": "background"
#         }
        
#         # Send to each registered device
#         for reg in device_registrations[key]:
#             push_token = reg["push_token"]
#             payload = json.dumps({"aps": {"content-available": 1}})
            
#             conn.request("POST", f"/3/device/{push_token}", payload, headers)
#             resp = conn.getresponse()
            
#             if resp.status != 200:
#                 logger.error(f"Failed to send push notification: {resp.status} {resp.reason}")
        
#         conn.close()
        
#     except Exception as e:
#         logger.error(f"Error sending push notifications: {str(e)}")

def create_apns_token(team_id, key_id, private_key_path):
    """Create JWT token for APNs authentication"""
    try:
        # Read the private key file
        with open(private_key_path, "rb") as key_file:
            private_key = key_file.read()
        
        # Create token headers
        token_headers = {
            "alg": "ES256",
            "kid": key_id
        }
        
        # Create token payload
        token_payload = {
            "iss": team_id,
            "iat": int(time.time())
        }
        
        # Sign and encode the JWT
        token = jwt.encode(
            token_payload,
            private_key,
            algorithm="ES256",
            headers=token_headers
        )
        
        return token
    except Exception as e:
        logger.error(f"Error creating APNs token: {str(e)}")
        raise

def has_pass_been_updated(digital_key, last_updated_str):
    """Check if the pass has been updated since the last client update"""
    try:
        # Parse the If-Modified-Since header
        last_updated = datetime.strptime(
            last_updated_str.strip(), 
            "%a, %d %b %Y %H:%M:%S %Z"
        ).replace(tzinfo=timezone.utc)
        
        # Use the key's updated_at timestamp or a related field
        # Assuming your model has an updated_at field, or use another relevant timestamp
        key_updated_at = digital_key.updated_at
        if not key_updated_at:
            return True
        
        # Make sure the timestamp has timezone info
        if key_updated_at.tzinfo is None:
            key_updated_at = key_updated_at.replace(tzinfo=timezone.utc)
        
        # Return True if the key has been updated since last client update
        return key_updated_at > last_updated
    except (ValueError, TypeError):
        # If there's any parsing error, assume the pass has been updated
        return True


def send_push_notifications_production(pass_type_id, serial_number, db=None):
    """Send push notifications to all devices registered for a pass (production)"""
    logger.info(f"Sending production push notifications for pass: {pass_type_id}:{serial_number}")
    
    # Get DB session if not provided
    close_db = False
    if db is None:
        from app.db.session import SessionLocal
        db = SessionLocal()
        close_db = True
    
    try:
        # Get all registered devices
        registrations = db.query(DeviceRegistration).filter(
            DeviceRegistration.pass_type_id == pass_type_id,
            DeviceRegistration.serial_number == serial_number,
            DeviceRegistration.active == True
        ).all()
        
        if not registrations:
            logger.warning(f"No registered devices found for pass: {serial_number}")
            return 0
        
        try:            
            # Create JWT token
            token = create_apns_token(
                team_id=settings.APPLE_TEAM_ID,
                key_id=settings.APPLE_PUSH_KEY_ID,
                private_key_path=settings.APPLE_PUSH_PRIVATE_KEY_PATH
            )
            
            # Setup APNs connection
            # to try found in official docs: "api.sandbox.push.apple.com" "api.development.push.apple.com"
            # server = "api.push.apple.com" if settings.PRODUCTION else "api.development.push.apple.com"
            print("server:", SERVER)
            base_url = f"https://{SERVER}/3/device/"
            
            # Track successful push notifications
            success_count = 0
            
            # Use httpx with HTTP/2
            with httpx.Client(http2=True) as client:
                for registration in registrations:
                    try:
                        device_token = registration.push_token
                        
                        # Set up headers
                        headers = {
                            "authorization": f"bearer {token}",
                            "apns-topic": settings.APPLE_PASS_TYPE_ID,
                            "apns-push-type": "background",
                            "apns-priority": "10"
                        }
                        
                        # Empty payload for pass updates
                        payload = {"aps": {}}
                        
                        # Send the request
                        url = base_url + device_token
                        response = client.post(url, json=payload, headers=headers)
                        
                        # Log response
                        if response.status_code == 200:
                            logger.info(f"Push notification sent successfully to device: {registration.device_library_id}")
                            success_count += 1
                            
                            # Create success event
                            key_event = KeyEvent(
                                key_id=registration.digital_key_id,
                                event_type="push_notification_sent",
                                device_info=f"Device: {registration.device_library_id}",
                                status="success",
                                details="Push notification sent successfully",
                                timestamp=datetime.now(timezone.utc)
                            )
                            db.add(key_event)
                            db.commit()
                        else:
                            logger.error(f"Failed to send push notification: {response.status_code} - {response.text}")
                            
                            # Create failure event
                            key_event = KeyEvent(
                                key_id=registration.digital_key_id,
                                event_type="push_notification_failed",
                                device_info=f"Device: {registration.device_library_id}",
                                status="error",
                                details=f"Status: {response.status_code}, Response: {response.text}"
                            )
                            db.add(key_event)
                            db.commit()
                            
                            # Handle token expiration
                            if response.status_code == 410:  # Gone - token is no longer valid
                                registration.active = False
                                db.commit()
                                logger.info(f"Marked registration as inactive due to invalid token: {registration.device_library_id}")
                    
                    except Exception as e:
                        logger.error(f"Error sending push notification: {str(e)}")
                        
                        # Create error event
                        try:
                            key_event = KeyEvent(
                                key_id=registration.digital_key_id,
                                event_type="push_notification_error",
                                device_info=f"Device: {registration.device_library_id}",
                                status="error",
                                details=f"Error: {str(e)}"
                            )
                            db.add(key_event)
                            db.commit()
                        except Exception as event_error:
                            logger.error(f"Failed to create error event: {str(event_error)}")
            
            logger.info(f"Push notifications completed: {success_count} successful out of {len(registrations)}")
            return success_count
        
        except Exception as e:
            logger.error(f"Fatal error in push notification service: {str(e)}")
            return 0
            
    finally:
        # Close DB session if we created it
        if close_db:
            db.close()

def save_auth_token_to_db(serial_number, auth_token, db):
    """Store authentication token for a digital key"""
    # Find the digital key by key_uuid (which is your serial_number)
    digital_key = db.query(DigitalKey).filter(
        DigitalKey.key_uuid == serial_number
    ).first()
    
    if digital_key:
        # Update auth token
        digital_key.auth_token = auth_token
        db.commit()
        db.refresh(digital_key)
        logger.info(f"Saved authentication token for key: {serial_number}")
        if digital_key.auth_token != auth_token:
            logger.error(f"Failed to update auth_token! Expected {auth_token}, got {digital_key.auth_token}")
        return auth_token
    else:
        logger.error(f"Digital key not found: {serial_number}")
        return None


# def verify_auth_token(serial_number, auth_token, db):
#     """Verify if authentication token is valid for a digital key"""
#     digital_key = db.query(DigitalKey).filter(
#         DigitalKey.key_uuid == serial_number,
#         DigitalKey.auth_token == auth_token
#     ).first()
#     print(digital_key, "heeere")
#     return digital_key is not None
def verify_auth_token(serial_number, auth_token, db):
    """Verify if authentication token is valid for a digital key"""
    print(f"Checking auth token for serial: {serial_number}, token: {auth_token}")
    
    # First check if key exists at all
    any_key = db.query(DigitalKey).filter(
        DigitalKey.key_uuid == serial_number
    ).first()
    
    print(f"Found digital key with this serial: {any_key is not None}")
    if any_key:
        print(f"Key details: id={any_key.id}, auth_token={any_key.auth_token}")
    
    # Original query
    digital_key = db.query(DigitalKey).filter(
        DigitalKey.key_uuid == serial_number,
        DigitalKey.auth_token == auth_token
    ).first()
    
    print(f"Match with auth token: {digital_key is not None}")
    
    return digital_key is not None
