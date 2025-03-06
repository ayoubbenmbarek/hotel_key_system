
from fastapi import APIRouter, Header,  HTTPException, Response, BackgroundTasks, Depends, Request
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import uuid
from typing import Optional
from datetime import datetime, timezone

from app.services.wallet_push_service import send_push_notifications, send_push_notifications_production
from app.models.device import DeviceRegistration
from app.models.digital_key import DigitalKey
from app.models.room import Room
from app.models.reservation import Reservation
from app.models.user import User
from app.services.wallet_service import create_wallet_pass, settings
from app.services.wallet_push_service import verify_auth_token, has_pass_been_updated

from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Store device registrations in memory (use database in production)
device_registrations = {}


@router.get("/apple/{pass_id}")
def get_apple_pass(pass_id: str):
    """
    Serve an Apple Wallet pass file
    """
    # Check if pass_id already contains the prefix and suffix
    if pass_id.startswith("hotelkey_") and pass_id.endswith(".pkpass"):
        # Extract the UUID portion
        uuid_part = pass_id.replace("hotelkey_", "").replace(".pkpass", "")
        pass_path = Path(f"app/static/passes/hotelkey_{uuid_part}.pkpass")
    else:
        # Use the pass_id as is (the UUID only)
        pass_path = Path(f"app/static/passes/hotelkey_{pass_id}.pkpass")
    
    if not pass_path.exists():
        raise HTTPException(status_code=404, detail="Pass not found")

    # For filename, always use the full format
    uuid_part = pass_id.replace("hotelkey_", "").replace(".pkpass", "")
    filename = f"hotelkey_{uuid_part}.pkpass"

    return FileResponse(
        str(pass_path),
        media_type="application/vnd.apple.pkpass",
        filename=filename,
        # Add required headers for Apple Wallet passes
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    )

@router.get("/google/{pass_id}")
def get_google_pass(pass_id: str):
    """
    Redirect to Google Wallet pass save link
    """
    # In a real implementation, this would generate a save link
    # For now, we'll just return a placeholder
    raise HTTPException(status_code=501, detail="Google Wallet integration not fully implemented")

# @router.get("/passes/{pass_type_id}/{serial_number}")
# async def get_latest_pass(
#     pass_type_id: str,
#     serial_number: str,
#     authorization: str = Header(None)
# ):
#     """Serve the latest version of a pass"""
#     # Get the token from the Authorization header
#     if not authorization or not authorization.startswith("ApplePass "):
#         raise HTTPException(status_code=401, detail="Invalid authorization")
    
#     auth_token = authorization.replace("ApplePass ", "")
    
#     # In a real implementation, verify the token matches the pass
#     # For now, we'll just check if the pass exists
    
#     pass_path = Path(f"app/static/passes/hotelkey_{serial_number}.pkpass")
#     if not pass_path.exists():
#         raise HTTPException(status_code=404, detail="Pass not found")
    
#     return Response(
#         content=open(pass_path, "rb").read(),
#         media_type="application/vnd.apple.pkpass",
#         headers={"Content-Disposition": f"attachment; filename=hotelkey_{serial_number}.pkpass"}
#     )
@router.get("/passes/{pass_type_id}/{serial_number}", response_model=None)
async def get_latest_pass(
    pass_type_id: str,
    serial_number: str,
    request: Request,
    db: Session = Depends(get_db),
    last_updated: Optional[str] = Header(None, alias="if-modified-since"),
):
    """Return the latest version of a pass"""
    logger.info(f"Pass update request: {pass_type_id}:{serial_number}")
    
    # Verify auth token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("ApplePass "):
        logger.error("Invalid authorization header in pass update request")
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    auth_token = auth_header.replace("ApplePass ", "")
    
    # Get the digital key
    digital_key = db.query(DigitalKey).filter(
        DigitalKey.key_uuid == serial_number,
        DigitalKey.auth_token == auth_token
    ).first()
    
    if not digital_key:
        logger.error(f"Invalid authentication token or key not found: {serial_number}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Check if pass has been modified since last update
    if last_updated and not has_pass_been_updated(digital_key, last_updated):
        return Response(status_code=304)  # Not Modified
    
    # Get all necessary data to create a pass
    reservation = db.query(Reservation).filter(Reservation.id == digital_key.reservation_id).first()
    if not reservation:
        logger.error(f"Reservation not found for key: {serial_number}")
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    user = db.query(User).filter(User.id == reservation.user_id).first()
    
    # Prepare pass data
    pass_data = {
        "key_uuid": digital_key.key_uuid,
        "room_number": room.room_number if room else "N/A",
        "guest_name": f"{user.first_name} {user.last_name}" if user else "Guest",
        "check_in": reservation.check_in.isoformat(),
        "check_out": reservation.check_out.isoformat(),
        "nfc_lock_id": room.nfc_lock_id if room else None,
        "is_active": digital_key.is_active
    }
    
    # Create a new .pkpass file
    pkpass_url = create_wallet_pass(pass_data, settings.APPLE_PASS_TYPE_ID)
    
    # Return the actual .pkpass file
    pkpass_filename = f"hotelkey_{serial_number}.pkpass"
    pkpass_path = Path(f"app/static/passes/{pkpass_filename}")
    
    if not pkpass_path.exists():
        logger.error(f"Pass file not found: {pkpass_path}")
        raise HTTPException(status_code=404, detail="Pass file not found")
    
    # Update last_used timestamp
    digital_key.last_used = datetime.now(timezone.utc)
    db.commit()
    
    return FileResponse(
        path=pkpass_path,
        media_type="application/vnd.apple.pkpass",
        filename=pkpass_filename
    )


# @router.post("/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
# async def register_device(
#     device_library_id: str,
#     pass_type_id: str,
#     serial_number: str,
#     push_token: str = Header(None)
# ):
#     """Register a device to receive push notifications for a pass"""
#     if not push_token:
#         raise HTTPException(status_code=400, detail="Push token is required")

#     # Store the registration
#     key = f"{pass_type_id}:{serial_number}"
#     if key not in device_registrations:
#         device_registrations[key] = []

#     # Add device if not already registered
#     if device_library_id not in [reg["device_id"] for reg in device_registrations[key]]:
#         device_registrations[key].append({
#             "device_id": device_library_id,
#             "push_token": push_token
#         })
    
#     return Response(status_code=201)
# @router.post("/{pass_type}/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
# # @router.post("/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
# async def register_device(
#     pass_type: str,  # 'apple' or 'google'
#     device_library_id: str,
#     pass_type_id: str,
#     serial_number: str,
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     """Register a device to receive push notifications for a digital key"""
#     logger.info(f"Registration request: Type={pass_type}, Pass={pass_type_id}:{serial_number}, Device={device_library_id}")

#     # logger.info(f"Registration request: Pass={pass_type_id}:{serial_number}, Device={device_library_id}")
    
#     # Extract headers
#     # push_token = request.headers.get("pushToken")
#     push_token = request.query_params.get("pushToken")  # Try query params first
#     if not push_token:
#         # Try various header formats
#         for header_name, value in request.headers.items():
#             if header_name.lower() in ["pushtoken", "push-token"]:
#                 push_token = value
#                 break

#     auth_header = request.headers.get("Authorization")
    
#     # Validate required headers
#     if not push_token:
#         logger.error("Missing push token in registration request")
#         raise HTTPException(status_code=400, detail="Push token is required")
    
#     if not auth_header or not auth_header.startswith("ApplePass "):
#         logger.error("Invalid authorization header in registration request")
#         raise HTTPException(status_code=401, detail="Invalid authentication")
    
#     # Extract and verify auth token
#     auth_token = auth_header.replace("ApplePass ", "")
#     if not verify_auth_token(serial_number, auth_token, db):
#         logger.error(f"Invalid authentication token for key: {serial_number}")
#         raise HTTPException(status_code=401, detail="Invalid authentication token")
    
#     # Get digital key
#     digital_key = db.query(DigitalKey).filter(
#         DigitalKey.key_uuid == serial_number
#     ).first()
    
#     if not digital_key:
#         logger.error(f"Digital key not found: {serial_number}")
#         raise HTTPException(status_code=404, detail="Key not found")
    
#     # Check if registration already exists
#     existing_registration = db.query(DeviceRegistration).filter(
#         DeviceRegistration.device_library_id == device_library_id,
#         DeviceRegistration.pass_type_id == pass_type_id,
#         DeviceRegistration.serial_number == serial_number
#     ).first()
    
#     if existing_registration:
#         # Update existing registration
#         existing_registration.push_token = push_token
#         existing_registration.active = True
#         existing_registration.updated_at = datetime.now(timezone.utc)
#         logger.info(f"Updated registration for device: {device_library_id}")
#     else:
#         # Create new registration
#         new_registration = DeviceRegistration(
#             device_library_id=device_library_id,
#             pass_type_id=pass_type_id,
#             serial_number=serial_number,
#             push_token=push_token,
#             digital_key_id=digital_key.id
#         )
#         db.add(new_registration)
#         logger.info(f"Created new registration for device: {device_library_id}")
    
#     db.commit()
#     logger.info(f"Device registration successful: {device_library_id} for key {serial_number}")
    
#     return Response(status_code=201)

# @router.delete("/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
# async def unregister_device(
#     device_library_id: str,
#     pass_type_id: str,
#     serial_number: str
# ):
#     """Unregister a device from a pass"""
#     key = f"{pass_type_id}:{serial_number}"
    
#     if key in device_registrations:
#         device_registrations[key] = [
#             reg for reg in device_registrations[key] 
#             if reg["device_id"] != device_library_id
#         ]
        
#         if not device_registrations[key]:
#             del device_registrations[key]
    
#     return Response(status_code=200)

# TODO for debug delete later placeholder etc
@router.post("/{pass_type}/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
async def register_device(
    pass_type: str,
    device_library_id: str,
    pass_type_id: str,
    serial_number: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a device to receive push notifications for a pass"""
    logger.info(f"Registration request: Type={pass_type}, Pass={pass_type_id}:{serial_number}, Device={device_library_id}")
    
    # Extract and verify auth token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("ApplePass "):
        logger.error("Invalid authorization header in registration request")
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    auth_token = auth_header.replace("ApplePass ", "")
    if not verify_auth_token(serial_number, auth_token, db):
        logger.error(f"Invalid authentication token for pass: {serial_number}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Extract push token from request body as JSON
    push_token = None
    try:
        body = await request.json()
        push_token = body.get("pushToken")
        logger.info(f"Found push token in JSON body: {push_token}")
    except Exception as e:
        logger.error(f"Error parsing request body as JSON: {str(e)}")
    
    # Validate required data
    if not push_token:
        logger.error("Missing push token in registration request")
        raise HTTPException(status_code=400, detail="Push token is required")
    
    # Check if registration already exists
    existing_reg = db.query(DeviceRegistration).filter(
        DeviceRegistration.device_library_id == device_library_id,
        DeviceRegistration.pass_type_id == pass_type_id,
        DeviceRegistration.serial_number == serial_number
    ).first()
    
    # Get the digital key
    digital_key = db.query(DigitalKey).filter(
        DigitalKey.key_uuid == serial_number
    ).first()
    
    if not digital_key:
        logger.error(f"Digital key not found: {serial_number}")
        raise HTTPException(status_code=404, detail="Digital key not found")
    
    if existing_reg:
        # Update existing registration
        existing_reg.push_token = push_token
        existing_reg.active = True
        existing_reg.updated_at = datetime.now()
        logger.info(f"Updated registration for device: {device_library_id}")
    else:
        # Create new registration
        new_reg = DeviceRegistration(
            id=str(uuid.uuid4()),
            device_library_id=device_library_id,
            pass_type_id=pass_type_id,
            serial_number=serial_number,
            push_token=push_token,
            active=True,
            digital_key_id=digital_key.id
        )
        db.add(new_reg)
        logger.info(f"Created new registration for device: {device_library_id}")
    
    db.commit()
    logger.info(f"Registration successful for device: {device_library_id}")
    
    return Response(status_code=201)

@router.delete("/{pass_type}/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
# @router.delete("/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
async def unregister_device(
    pass_type: str,  # 'apple' or 'google'
    device_library_id: str,
    pass_type_id: str,
    serial_number: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Unregister a device from receiving push notifications for a pass"""
    logger.info(f"Unregistration request: Pass={pass_type_id}:{serial_number}, Device={device_library_id}")
    
    # Extract and verify auth token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("ApplePass "):
        logger.error("Invalid authorization header in unregistration request")
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    auth_token = auth_header.replace("ApplePass ", "")
    if not verify_auth_token(serial_number, auth_token, db):
        logger.error(f"Invalid authentication token for pass: {serial_number}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # Find and update the registration
    registration = db.query(DeviceRegistration).filter(
        DeviceRegistration.device_library_id == device_library_id,
        DeviceRegistration.pass_type_id == pass_type_id,
        DeviceRegistration.serial_number == serial_number
    ).first()
    
    if registration:
        # Soft delete - mark as inactive
        registration.active = False
        registration.updated_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Device unregistered: {device_library_id} for pass {serial_number}")
    else:
        logger.warning(f"No registration found to unregister: {device_library_id} for pass {serial_number}")
    
    return Response(status_code=200)

@router.get("/devices/{device_id}/registrations/{pass_type_id}")
async def get_serial_numbers(
    device_id: str,
    pass_type_id: str
):
    """Get all passes registered for a device"""
    serial_numbers = []
    
    for key, registrations in device_registrations.items():
        type_id, serial = key.split(":")
        if type_id == pass_type_id:
            if any(reg["device_id"] == device_id for reg in registrations):
                serial_numbers.append(serial)
    
    return {"serialNumbers": serial_numbers}

@router.post("/passes/{pass_type_id}/{serial_number}/update")
async def update_pass(
    pass_type_id: str,
    serial_number: str,
    update_data: dict,
    background_tasks: BackgroundTasks
):
    """Update a pass and send push notification to devices"""
    # Find the pass file
    pass_path = Path(f"app/static/passes/hotelkey_{serial_number}.pkpass")
    if not pass_path.exists():
        raise HTTPException(status_code=404, detail="Pass not found")
    
    # For a real implementation, you would:
    # 1. Extract the pass.json from the .pkpass file (it's a zip)
    # 2. Update the pass.json with the new data
    # 3. Re-sign the pass and create a new .pkpass file
    # 4. Send push notifications to registered devices
    
    # For demonstration, we'll simulate updating the pass
    background_tasks.add_task(send_push_notifications, pass_type_id, serial_number)
    
    return {"status": "updating", "message": "Pass update initiated"}
