# wallet_push_service.py
import json
import logging
from pathlib import Path
import jwt
import time
import http.client
import uuid

from app.config import settings

logger = logging.getLogger(__name__)

device_registrations = {}

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

def send_push_notifications_production(pass_type_id, serial_number):
    """Send push notifications to all devices registered for a pass (production)"""
    try:
        key = f"{pass_type_id}:{serial_number}"
        if key not in device_registrations:
            return
        
        # Load your APNS authentication key
        with open(settings.APPLE_PUSH_KEY_PATH, 'r') as key_file:
            auth_key = key_file.read()
        
        # Create a JWT token for APNS authentication
        token = jwt.encode(
            {
                'iss': settings.APPLE_TEAM_ID,
                'iat': time.time()
            },
            auth_key,
            algorithm='ES256',
            headers={
                'kid': settings.APPLE_PUSH_KEY_ID
            }
        )
        
        # Set up APNS connection
        conn = http.client.HTTPSConnection("api.push.apple.com" if settings.PRODUCTION else "api.development.push.apple.com")
        
        headers = {
            "authorization": f"bearer {token}",
            "apns-topic": f"pass.{pass_type_id}",
            "apns-push-type": "background"
        }
        
        # Send to each registered device
        for reg in device_registrations[key]:
            push_token = reg["push_token"]
            payload = json.dumps({"aps": {"content-available": 1}})
            
            conn.request("POST", f"/3/device/{push_token}", payload, headers)
            resp = conn.getresponse()
            
            if resp.status != 200:
                logger.error(f"Failed to send push notification: {resp.status} {resp.reason}")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error sending push notifications: {str(e)}")
