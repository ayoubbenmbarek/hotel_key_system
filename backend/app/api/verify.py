# backend/app/api/verify.py
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pytz

from app.db.session import get_db
from app.models.digital_key import DigitalKey
from app.models.key_event import KeyEvent, EventType
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.user import User
from app.schemas.digital_key import KeyVerificationRequest, KeyVerification

router = APIRouter()


@router.post("/key", response_model=KeyVerification)
def verify_key(
    *,
    db: Session = Depends(get_db),
    verification: KeyVerificationRequest
) -> Any:
    """
    Verify a digital key for door access
    
    This endpoint is called by the door lock system to verify if a key is valid
    """
    # Find key by UUID
    key = db.query(DigitalKey).filter(DigitalKey.key_uuid == verification.key_uuid).first()

    # Create event record
    local_tz = pytz.timezone('Europe/Paris')
    now = datetime.now(local_tz)
    
    # Create initial access attempt event
    event = KeyEvent(
        key_id=key.id if key else None,
        event_type=EventType.PHYSICAL_ACCESS_ATTEMPT,
        device_info=verification.device_info,
        timestamp=now,
        location=verification.location,
        status="pending",
        details=f"Lock ID: {verification.lock_id}"
    )
    db.add(event)
    db.commit()

    # Check if key exists
    if not key:
        event.status = "failure"
        event.event_type = EventType.PHYSICAL_ACCESS_DENIED
        event.details = "Key not found"
        db.add(event)
        db.commit()
        
        return {
            "is_valid": False,
            "message": "Key not found"
        }

    # Check if key is active
    if not key.is_active:
        event.status = "failure"
        event.event_type = EventType.PHYSICAL_ACCESS_DENIED
        event.details = "Key is inactive"
        db.add(event)
        db.commit()
        
        return {
            "is_valid": False,
            "message": "Key is inactive"
        }

    # For key validation
    valid_from = key.valid_from
    valid_until = key.valid_until

    # Check key validity period
    # If dates from database don't have timezone info
    if valid_from.tzinfo is None:
        # First convert to datetime with local timezone
        valid_from = local_tz.localize(valid_from)

    if valid_until.tzinfo is None:
        # First convert to datetime with local timezone
        valid_until = local_tz.localize(valid_until)

    if now < valid_from or now > valid_until:
        event.status = "failure"
        event.event_type = EventType.PHYSICAL_ACCESS_DENIED
        event.details = "Key outside validity period"
        db.add(event)
        db.commit()

        return {
            "is_valid": False,
            "message": "Key outside validity period"
        }

    # Get reservation and room info
    reservation = db.query(Reservation).filter(
        Reservation.id == key.reservation_id
    ).first()
    
    if not reservation or reservation.status not in ["confirmed", "checked_in"]:
        event.status = "failure"
        event.event_type = EventType.PHYSICAL_ACCESS_DENIED
        event.details = f"Invalid reservation status: {reservation.status if reservation else 'None'}"
        db.add(event)
        db.commit()
        
        return {
            "is_valid": False,
            "message": "Reservation not valid"
        }
    
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    
    # Verify the lock ID matches
    if room.nfc_lock_id != verification.lock_id:
        event.status = "failure"
        event.event_type = EventType.PHYSICAL_ACCESS_DENIED
        event.details = f"Lock ID mismatch: Expected {room.nfc_lock_id}, got {verification.lock_id}"
        db.add(event)
        db.commit()
        
        return {
            "is_valid": False,
            "message": "Invalid lock for this key"
        }
    
    # Get user info
    user = db.query(User).filter(User.id == reservation.user_id).first()
    
    # Update key last used timestamp and access count
    key.last_used = now
    key.access_count += 1
    db.add(key)
    
    # Update event status for successful access
    event.status = "success"
    event.event_type = EventType.PHYSICAL_ACCESS_GRANTED
    event.details = f"Access granted to room {room.room_number} for {user.first_name} {user.last_name}"
    db.add(event)
    
    db.commit()
    
    return {
        "is_valid": True,
        "message": "Access granted",
        "room_number": room.room_number,
        "guest_name": f"{user.first_name} {user.last_name}" if user else None
    }
