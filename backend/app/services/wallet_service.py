# backend/app/services/wallet_service.py
import json
import logging
import os
import uuid
import tempfile
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
import base64
import hmac
import hashlib
import requests

from app.config import settings
from app.models.digital_key import KeyType

# Configure logging
logger = logging.getLogger(__name__)


def create_wallet_pass(pass_data, pass_type):
    """
    Create a wallet pass based on the requested type
    """
    if pass_type == KeyType.APPLE:
        return create_apple_wallet_pass(pass_data)
    elif pass_type == KeyType.GOOGLE:
        return create_google_wallet_pass(pass_data)
    else:
        raise ValueError(f"Unsupported pass type: {pass_type}")


def create_apple_wallet_pass(pass_data):
    """
    Create an Apple Wallet pass for hotel room key
    
    This implementation creates a .pkpass file for Apple Wallet
    """
    try:
        logger.info(f"Creating Apple Wallet pass for key: {pass_data['key_uuid']}")
        
        # Create a temporary directory to build the pass
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create pass.json structure
            pass_json = {
                "formatVersion": 1,
                "passTypeIdentifier": settings.APPLE_PASS_TYPE_ID,
                "teamIdentifier": settings.APPLE_TEAM_ID,
                "organizationName": settings.HOTEL_NAME,
                "description": f"Room Key for {settings.HOTEL_NAME}",
                "foregroundColor": "rgb(255, 255, 255)",
                "backgroundColor": "rgb(44, 62, 80)",
                "labelColor": "rgb(255, 255, 255)",
                "logoText": settings.HOTEL_NAME,
                "generic": {
                    "primaryFields": [
                        {
                            "key": "roomNumber",
                            "label": "ROOM",
                            "value": pass_data["room_number"]
                        }
                    ],
                    "secondaryFields": [
                        {
                            "key": "guestName",
                            "label": "GUEST",
                            "value": pass_data["guest_name"]
                        }
                    ],
                    "auxiliaryFields": [
                        {
                            "key": "checkIn",
                            "label": "CHECK-IN",
                            "value": pass_data["check_in"],
                            "dateStyle": "PKDateStyleMedium"
                        },
                        {
                            "key": "checkOut",
                            "label": "CHECK-OUT",
                            "value": pass_data["check_out"],
                            "dateStyle": "PKDateStyleMedium"
                        }
                    ]
                },
                "nfc": {
                    "message": f"Room Key: {pass_data['room_number']}",
                    "encryptionPublicKey": pass_data["key_uuid"]
                },
                "barcodes": [
                    {
                        "message": pass_data["key_uuid"],
                        "format": "PKBarcodeFormatQR",
                        "messageEncoding": "utf-8"
                    }
                ],
                "expirationDate": pass_data["check_out"],
                "voided": False
            }
            
            # Write pass.json to temporary directory
            with open(temp_path / "pass.json", "w") as f:
                json.dump(pass_json, f, indent=2)
            
            # In a real implementation, you would:
            # 1. Copy required images (icon, logo, etc.) to temp directory
            # 2. Create a manifest.json with SHA-1 hashes of all files
            # 3. Sign the manifest with your certificate to create signature
            # 4. Create a .pkpass file (zip archive with specific format)
            
            # For this demo, we'll skip these steps and simulate the URL
            
            # Generate a unique filename for the pass
            filename = f"hotelkey_{pass_data['key_uuid']}.pkpass"
            
            # In production, the pass would be stored in cloud storage and a URL returned
            pass_url = f"{settings.PASS_BASE_URL}/apple/{filename}"
            
            logger.info(f"Apple Wallet pass created successfully: {pass_url}")
            return pass_url
            
    except Exception as e:
        logger.error(f"Failed to create Apple Wallet pass: {str(e)}")
        raise


def create_google_wallet_pass(pass_data):
    """
    Create a Google Wallet pass for hotel room key
    
    This implementation creates a Google Wallet pass
    """
    try:
        logger.info(f"Creating Google Wallet pass for key: {pass_data['key_uuid']}")
        
        # Create Google Wallet pass JSON
        pass_json = {
            "id": f"{settings.GOOGLE_PAY_ISSUER_ID}.{pass_data['key_uuid']}",
            "classId": f"{settings.GOOGLE_PAY_ISSUER_ID}.hotel_key_class",
            "genericType": "GENERIC_TYPE_HOTEL_KEY",
            "hexBackgroundColor": "#2c3e50",
            "logo": {
                "sourceUri": {
                    "uri": settings.HOTEL_LOGO_URL
                }
            },
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": "Room Key"
                }
            },
            "header": {
                "defaultValue": {
                    "language": "en-US",
                    "value": settings.HOTEL_NAME
                }
            },
            "textModulesData": [
                {
                    "id": "room_number",
                    "header": "Room",
                    "body": pass_data["room_number"]
                },
                {
                    "id": "guest_name",
                    "header": "Guest",
                    "body": pass_data["guest_name"]
                },
                {
                    "id": "check_in",
                    "header": "Check-in",
                    "body": pass_data["check_in"]
                },
                {
                    "id": "check_out",
                    "header": "Check-out",
                    "body": pass_data["check_out"]
                }
            ],
            "barcode": {
                "type": "QR_CODE",
                "value": pass_data["key_uuid"]
            },
            "nfcInfo": {
                "enabled": True,
                "message": pass_data["key_uuid"]
            },
            "validTimeInterval": {
                "start": {
                    "date": pass_data["check_in"]
                },
                "end": {
                    "date": pass_data["check_out"]
                }
            },
            "state": "ACTIVE"
        }
        
        # In a real implementation, you would:
        # 1. Use Google's API to create the pass
        # 2. Return a save link or pass URL
        
        # For this demo, we'll simulate the URL
        
        # Generate a unique ID for the pass
        pass_id = f"g-{pass_data['key_uuid']}"
        
        # In production, the pass would be created via Google Pay API and a URL returned
        pass_url = f"{settings.PASS_BASE_URL}/google/{pass_id}"
        
        logger.info(f"Google Wallet pass created successfully: {pass_url}")
        return pass_url
        
    except Exception as e:
        logger.error(f"Failed to create Google Wallet pass: {str(e)}")
        raise
