from fastapi import APIRouter, Header,  HTTPException, Response, BackgroundTasks
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from app.services.wallet_push_service import send_push_notifications, send_push_notifications_production

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

@router.get("/passes/{pass_type_id}/{serial_number}")
async def get_latest_pass(
    pass_type_id: str,
    serial_number: str,
    authorization: str = Header(None)
):
    """Serve the latest version of a pass"""
    # Get the token from the Authorization header
    if not authorization or not authorization.startswith("ApplePass "):
        raise HTTPException(status_code=401, detail="Invalid authorization")
    
    auth_token = authorization.replace("ApplePass ", "")
    
    # In a real implementation, verify the token matches the pass
    # For now, we'll just check if the pass exists
    
    pass_path = Path(f"app/static/passes/hotelkey_{serial_number}.pkpass")
    if not pass_path.exists():
        raise HTTPException(status_code=404, detail="Pass not found")
    
    return Response(
        content=open(pass_path, "rb").read(),
        media_type="application/vnd.apple.pkpass",
        headers={"Content-Disposition": f"attachment; filename=hotelkey_{serial_number}.pkpass"}
    )

@router.post("/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
async def register_device(
    device_library_id: str,
    pass_type_id: str,
    serial_number: str,
    push_token: str = Header(None)
):
    """Register a device to receive push notifications for a pass"""
    if not push_token:
        raise HTTPException(status_code=400, detail="Push token is required")
    
    # Store the registration
    key = f"{pass_type_id}:{serial_number}"
    if key not in device_registrations:
        device_registrations[key] = []
    
    # Add device if not already registered
    if device_library_id not in [reg["device_id"] for reg in device_registrations[key]]:
        device_registrations[key].append({
            "device_id": device_library_id,
            "push_token": push_token
        })
    
    return Response(status_code=201)

@router.delete("/devices/{device_library_id}/registrations/{pass_type_id}/{serial_number}")
async def unregister_device(
    device_library_id: str,
    pass_type_id: str,
    serial_number: str
):
    """Unregister a device from a pass"""
    key = f"{pass_type_id}:{serial_number}"
    
    if key in device_registrations:
        device_registrations[key] = [
            reg for reg in device_registrations[key] 
            if reg["device_id"] != device_library_id
        ]
        
        if not device_registrations[key]:
            del device_registrations[key]
    
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
