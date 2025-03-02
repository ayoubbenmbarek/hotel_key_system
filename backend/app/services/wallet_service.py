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
    
    This implementation creates a real .pkpass file for Apple Wallet
    """
    try:
        logger.info(f"Creating Apple Wallet pass for key: {pass_data['key_uuid']}")
        
        # Create a temporary directory to build the pass
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            check_in_dt = datetime.fromisoformat(pass_data['check_in']).replace(microsecond=0)
            formatted_check_in = check_in_dt.strftime('%Y-%m-%dT%H:%M:%SZ')

            # Similarly for check_out
            check_out_dt = datetime.fromisoformat(pass_data['check_out']).replace(microsecond=0)
            formatted_check_out = check_out_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            pkpass_filename = f"hotelkey_{pass_data['key_uuid']}.pkpass"
            # Create pass.json structure
            pass_json = {
                "formatVersion": 1,
                "passTypeIdentifier": settings.APPLE_PASS_TYPE_ID,
                "teamIdentifier": settings.APPLE_TEAM_ID,
                "serialNumber": pass_data["key_uuid"],
                "organizationName": settings.HOTEL_NAME,
                "description": f"Room Key for {settings.HOTEL_NAME}",
                
                # Fixed color formatting
                "foregroundColor": "rgb(255, 255, 255)",
                "backgroundColor": "rgb(44, 62, 80)",
                
                "labelColor": "rgb(255, 255, 255)",
                "logoText": settings.HOTEL_NAME,
                # TODO: test update checkout date in real time in pc laptop:
                # TODO add logo expired after some time
                # TODO add ads in wallet for customers
                # TODO add frontend for admin and staff to manipulate cards and reservations
                # TODO checks if email sent successfully otherwise send with ather email or retry
                # TODO: send link contains two ad to wallet android and apple
                # Locations configuration
                "locations": [
                    {
                        "longitude": -122.3748889,
                        "latitude": 37.6189722,
                        "relevantText": "Welcome to Palacio Holding Hotel! Your digital key is ready to use."
                    }
                ],
                
                # Generic pass structure
                "generic": {
                    "primaryFields": [
                        {
                            "key": "roomNumber",
                            "label": "ROOM",
                            "value": pass_data.get('room_number', 'N/A'),
                            "textAlignment": pass_data.get(
                                'room_number_alignment', 
                                "PKTextAlignmentCenter"
                            )
                        }
                    ],
                    "secondaryFields": [
                        {
                            "key": "guestName",
                            "label": "GUEST",
                            "value": pass_data.get('guest_name', 'Guest')
                        },
                        {
                            "key": "hotelName",
                            "label": "HOTEL",
                            "value": pass_data.get(
                                'hotel_display_name', 
                                settings.HOTEL_NAME
                            )
                        }
                    ],
                    "auxiliaryFields": [
                        {
                            "key": "checkIn",
                            "label": "CHECK-IN",
                            "value": formatted_check_in,
                            # "dateStyle": "PKDateStyleMedium",
                            # "timeStyle": "PKTimeStyleShort"
                        },
                        {
                            "key": "checkOut",
                            "label": "CHECK-OUT",
                            "value": formatted_check_out,
                            # "dateStyle": "PKDateStyleMedium",
                            # "timeStyle": "PKTimeStyleShort"
                        }
                    ],
                    # Optional back fields for additional information
                    "backFields": pass_data.get('back_fields', [
                        {
                            "key": "checkInDate",
                            "label": "Check-In Date",
                            "value": formatted_check_in
                        },
                        {
                            "key": "checkOutDate",
                            "label": "Check-Out Date", 
                            "value": formatted_check_out
                        },
                        {
                            "key": "instructions",
                            "label": "HOW TO USE",
                            "value": "Hold your phone near the door lock to unlock your room. Your digital key will work from check-in until check-out time."
                        },
                        {
                            "key": "terms",
                            "label": "TERMS & CONDITIONS",
                            "value": "This digital key provides access to your assigned room for the duration of your stay. The key is non-transferable and will expire automatically at check-out time."
                        }
                    ])
                },
                
                # Barcode configuration
                "barcodes": [
                    {
                        "message": f"{settings.PASS_BASE_URL}/apple/{pkpass_filename}",
                        "format": "PKBarcodeFormatQR",
                        "messageEncoding": "utf-8",
                        "altText": f"Room {pass_data.get('room_number', 'N/A')}"
                    }
                ],
                
                "relevantDate": formatted_check_in,
                "expirationDate": formatted_check_out,
                "voided": not pass_data.get('is_active', True),
                
                # Optional web service URL for pass updates
                # "webServiceURL": pass_data.get(
                #     'web_service_url',
                #     "https://localhost:8000/api/v1/passes/"
                # ),
                # "webServiceURL": settings.PASS_BASE_URL,
                # "authenticationToken": pass_data["key_uuid"]
            }

            # In production, the pass would be stored in cloud storage and a URL returned
            # Write pass.json to temporary directory
            with open(temp_path / "pass.json", "w") as f:
                json.dump(pass_json, f, indent=2)
            
            # Copy required images from assets directory to pass directory
            # In a real implementation, you would have these images in your project
            images_dir = Path("app/static/pass_images")
            for image_file in ["icon.png", "icon@2x.png", "logo.png", "logo@2x.png"]:
                if (images_dir / image_file).exists():
                    shutil.copy(images_dir / image_file, temp_path / image_file)
                else:
                    logger.warning(f"Missing pass image: {image_file}")
            
            # Create manifest.json with SHA-1 hashes of all files
            manifest = {}
            for file_path in temp_path.glob("*"):
                if file_path.name not in ["manifest.json", "signature"]:
                    with open(file_path, "rb") as f:
                        file_data = f.read()
                        manifest[file_path.name] = hashlib.sha1(file_data).hexdigest()
            
            with open(temp_path / "manifest.json", "w") as f:
                json.dump(manifest, f)
            
            # Sign the manifest with your certificate to create signature
            certificate_path = Path(settings.APPLE_CERT_PATH)
            key_path = Path(settings.APPLE_KEY_PATH)
            wwdr_path = Path(settings.APPLE_WWDR_PATH)
            
            # Check if certificates exist
            if not (certificate_path.exists() and key_path.exists() and wwdr_path.exists()):
                raise FileNotFoundError("Apple Wallet certificates not found")
            
            # Create signature using OpenSSL
            signature_path = temp_path / "signature"
            manifest_path = temp_path / "manifest.json"
            
            # Execute OpenSSL command to create signature
            openssl_cmd = [
                "openssl", "smime", "-sign", "-binary",
                "-signer", str(certificate_path),
                "-certfile", str(wwdr_path),
                "-inkey", str(key_path),
                "-in", str(manifest_path),
                "-out", str(signature_path),
                "-outform", "DER"
            ]
            
            subprocess.run(openssl_cmd, check=True)
            
            # Create .pkpass file (zip archive)
            output_dir = Path("app/static/passes")
            output_dir.mkdir(exist_ok=True, parents=True)
            
            # pkpass_filename = f"hotelkey_{pass_data['key_uuid']}.pkpass"
            pkpass_path = output_dir / pkpass_filename
            
            # Create zip archive (.pkpass)
            shutil.make_archive(
                str(pkpass_path).replace(".pkpass", ""),
                'zip',
                temp_dir
            )
            
            # Rename .zip to .pkpass
            if pkpass_path.with_suffix('.zip').exists():
                shutil.move(
                    pkpass_path.with_suffix('.zip'),
                    pkpass_path
                )
            
            # Set up URL where the pass can be downloaded
            pass_url = f"{settings.PASS_BASE_URL}/apple/{pkpass_filename}"
            
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
