# backend/app/services/verification_service.py
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

from sqlalchemy.orm import Session

from app.models.digital_key import DigitalKey
from app.models.key_event import KeyEvent
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.user import User

logger = logging.getLogger(__name__)


def verify_key_access(
    db: Session,
    key_uuid: str,
    lock_id: str,
    device_info: Optional[str] = None,
    location: Optional[str] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify if a digital key can access a specific lock
    
    Args:
        db: Database session
        key_uuid: Unique identifier for the key
        lock_id: Identifier for the lock (door)
        device_info: Information about the device trying to access
        location: Location information
    
    Returns:
        Tuple containing:
        - Boolean indicating if access is granted
        - Message explaining the verification result
        - Dictionary with additional data (room number, guest name, etc.)
    """
    # Find key by UUID
    key = db.query(DigitalKey).filter(DigitalKey.key_uuid == key_uuid).first()
    
    # Create event record
    now = datetime.now(timezone.utc)
    event = None
    
    if key:
        event = KeyEvent(
            key_id=key.id,
            event_type="access_attempt",
            device_info=device_info,
            timestamp=now,
            location=location,
            status="pending",
            details=f"Lock ID: {lock_id}"
        )
        db.add(event)
        db.commit()
    
    # If key doesn't exist
    if not key:
        logger.warning(f"Access attempt with non-existent key UUID: {key_uuid}")
        if event:
            event.status = "failure"
            event.details = "Key not found"
            db.add(event)
            db.commit()
        
        return False, "Key not found", {}
    
    # Check if key is active
    if not key.is_active:
        logger.warning(f"Access attempt with inactive key: {key_uuid}")
        event.status = "failure"
        event.details = "Key is inactive"
        db.add(event)
        db.commit()
        
        return False, "Key is inactive", {}
    
    # Check key validity period
    if now < key.valid_from or now > key.valid_until:
        logger.warning(f"Access attempt with key outside validity period: {key_uuid}")
        event.status = "failure"
        event.details = "Key outside validity period"
        db.add(event)
        db.commit()
        
        return False, "Key outside validity period", {}
    
    # Get reservation
    reservation = db.query(Reservation).filter(
        Reservation.id == key.reservation_id
    ).first()
    
    if not reservation or reservation.status not in ["confirmed", "checked_in"]:
        logger.warning(f"Access attempt with invalid reservation: {key.reservation_id}")
        event.status = "failure"
        event.details = f"Invalid reservation status: {reservation.status if reservation else 'None'}"
        db.add(event)
        db.commit()
        
        return False, "Reservation not valid", {}
    
    # Get room
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    
    # Verify the lock ID matches
    if room.nfc_lock_id != lock_id:
        logger.warning(f"Access attempt with key {key_uuid} on wrong lock {lock_id}, expected {room.nfc_lock_id}")
        event.status = "failure"
        event.details = f"Lock ID mismatch: Expected {room.nfc_lock_id}, got {lock_id}"
        db.add(event)
        db.commit()
        
        return False, "Invalid lock for this key", {}
    
    # Get user info
    user = db.query(User).filter(User.id == reservation.user_id).first()
    
    # Update key last used timestamp and access count
    key.last_used = now
    key.access_count += 1
    db.add(key)
    
    # Update event status
    event.status = "success"
    event.details = f"Access granted to room {room.room_number}"
    db.add(event)
    
    db.commit()
    
    logger.info(f"Access granted to room {room.room_number} with key {key_uuid}")
    
    return True, "Access granted", {
        "room_number": room.room_number,
        "guest_name": f"{user.first_name} {user.last_name}" if user else "Unknown",
        "hotel_id": room.hotel_id,
        "room_id": room.id,
        "reservation_id": reservation.id,
        "key_id": key.id
    }


def log_key_usage(
    db: Session,
    key_id: str,
    event_type: str,
    device_info: Optional[str] = None,
    location: Optional[str] = None,
    status: str = "success",
    details: Optional[str] = None
) -> Optional[KeyEvent]:
    """
    Log key usage event
    
    Args:
        db: Database session
        key_id: Digital key ID
        event_type: Type of event (access_attempt, key_activated, etc.)
        device_info: Information about the device
        location: Location information
        status: Event status (success, failure)
        details: Additional details
    
    Returns:
        Created KeyEvent object or None if error
    """
    try:
        # Verify key exists
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            logger.error(f"Cannot log event for non-existent key ID: {key_id}")
            return None
        
        # Create event
        event = KeyEvent(
            key_id=key_id,
            event_type=event_type,
            device_info=device_info,
            timestamp=datetime.now(timezone.utc),
            location=location,
            status=status,
            details=details
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
    
    except Exception as e:
        logger.error(f"Error logging key event: {str(e)}")
        return None
