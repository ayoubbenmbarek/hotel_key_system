# backend/app/services/key_service.py
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from sqlalchemy.orm import Session

from app.models.digital_key import DigitalKey, KeyStatus, KeyType, KeyEvent
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from app.models.user import User
from app.services.wallet_service import create_wallet_pass
from app.services.email_service import send_key_email

logger = logging.getLogger(__name__)


# def create_digital_key(
#     db: Session,
#     reservation_id: str,
#     pass_type: KeyType,
#     send_email: bool = True
# ) -> Tuple[DigitalKey, str]:
#     """
#     Create a new digital key for a reservation
    
#     Args:
#         db: Database session
#         reservation_id: Reservation ID
#         pass_type: Type of wallet pass (apple, google)
#         send_email: Whether to send the key via email
    
#     Returns:
#         Tuple of (DigitalKey object, pass_url)
    
#     Raises:
#         ValueError: If reservation is invalid or issues with creating the key
#     """
#     try:
#         # Check if reservation exists
#         reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
#         if not reservation:
#             raise ValueError("Reservation not found")
        
#         # Verify reservation status
#         if reservation.status not in [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]:
#             raise ValueError(f"Cannot create key for reservation with status: {reservation.status}")
        
#         # Get user and room info
#         user = db.query(User).filter(User.id == reservation.user_id).first()
#         if not user:
#             raise ValueError("User not found")
        
#         room = db.query(Room).filter(Room.id == reservation.room_id).first()
#         if not room:
#             raise ValueError("Room not found")
        
#         # Generate unique key UUID
#         key_uuid = str(uuid.uuid4())
        
#         # Create pass data for wallet pass
#         pass_data = {
#             "key_uuid": key_uuid,
#             "hotel_name": db.query(Room).join(Room.hotel).filter(Room.id == reservation.room_id).first().hotel.name,
#             "room_number": room.room_number,
#             "guest_name": f"{user.first_name} {user.last_name}",
#             "check_in": reservation.check_in.isoformat(),
#             "check_out": reservation.check_out.isoformat(),
#             "nfc_lock_id": room.nfc_lock_id
#         }
        
#         # Create wallet pass
#         try:
#             pass_url = create_wallet_pass(pass_data, pass_type)
#         except Exception as e:
#             logger.error(f"Error creating wallet pass: {str(e)}")
#             raise ValueError(f"Error creating wallet pass: {str(e)}")
        
#         # Create digital key record
#         digital_key = DigitalKey(
#             reservation_id=reservation_id,
#             key_uuid=key_uuid,
#             pass_url=pass_url,
#             pass_type=pass_type,
#             valid_from=reservation.check_in,
#             valid_until=reservation.check_out,
#             is_active=True,
#             status=KeyStatus.CREATED,
#             auth_token=key_uuid
#         )
        
#         db.add(digital_key)
#         db.commit()
#         db.refresh(digital_key)
        
#         # Send email if requested
#         if send_email:
#             success = send_key_email(
#                 user.email,
#                 f"{user.first_name} {user.last_name}",
#                 pass_url,
#                 digital_key.id,
#                 pass_data
#             )
            
#             if not success:
#                 logger.warning(f"Failed to send key email to {user.email}")
#                 # Don't fail the key creation if email sending fails
        
#         # Log key creation
#         event = KeyEvent(
#             key_id=digital_key.id,
#             event_type="key_created",
#             timestamp=datetime.now(timezone.utc),
#             status="success"
#         )
#         db.add(event)
#         db.commit()
        
#         return digital_key, pass_url
    
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Error creating digital key: {str(e)}")
#         raise ValueError(f"Error creating digital key: {str(e)}")


def activate_key(db: Session, key_id: str) -> DigitalKey:
    """
    Activate a digital key
    
    Args:
        db: Database session
        key_id: Key ID
    
    Returns:
        Updated DigitalKey object
    
    Raises:
        ValueError: If key not found or already active
    """
    try:
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            raise ValueError("Digital key not found")
        
        if key.is_active and key.status == KeyStatus.ACTIVE:
            raise ValueError("Key is already active")
        
        # Activate the key
        key.is_active = True
        key.status = KeyStatus.ACTIVE
        key.activated_at = datetime.now(timezone.utc)
        
        # Log activation
        event = KeyEvent(
            key_id=key.id,
            event_type="key_activated",
            timestamp=datetime.now(timezone.utc),
            status="success"
        )
        
        db.add(key)
        db.add(event)
        db.commit()
        db.refresh(key)
        
        return key
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating key: {str(e)}")
        raise ValueError(f"Error activating key: {str(e)}")


def deactivate_key(db: Session, key_id: str) -> DigitalKey:
    """
    Deactivate a digital key
    
    Args:
        db: Database session
        key_id: Key ID
    
    Returns:
        Updated DigitalKey object
    
    Raises:
        ValueError: If key not found
    """
    try:
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            raise ValueError("Digital key not found")
        
        # Deactivate the key
        key.is_active = False
        key.status = KeyStatus.REVOKED
        
        # Log deactivation
        event = KeyEvent(
            key_id=key.id,
            event_type="key_deactivated",
            timestamp=datetime.now(timezone.utc),
            status="success"
        )
        
        db.add(key)
        db.add(event)
        db.commit()
        db.refresh(key)
        
        return key
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error deactivating key: {str(e)}")
        raise ValueError(f"Error deactivating key: {str(e)}")


# def extend_key_validity(db: Session, key_id: str, new_end_date: datetime) -> DigitalKey:
#     """
#     Extend the validity period of a digital key
    
#     Args:
#         db: Database session
#         key_id: Key ID
#         new_end_date: New end date for the key
    
#     Returns:
#         Updated DigitalKey object
    
#     Raises:
#         ValueError: If key not found or new date is invalid
#     """
#     try:
#         key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
#         if not key:
#             raise ValueError("Digital key not found")
        
#         # Validate new end date
#         if new_end_date <= key.valid_from:
#             raise ValueError("New end date must be after the start date")
        
#         if new_end_date <= datetime.now(timezone.utc):
#             raise ValueError("New end date must be in the future")
        
#         # Update key validity
#         key.valid_until = new_end_date
        
#         # Also update the reservation check-out date
#         reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
#         if reservation:
#             reservation.check_out = new_end_date
#             db.add(reservation)
        
#         # Log extension
#         event = KeyEvent(
#             key_id=key.id,
#             event_type="key_extended",
#             timestamp=datetime.now(timezone.utc),
#             status="success",
#             details=f"Extended until: {new_end_date.isoformat()}"
#         )
        
#         db.add(key)
#         db.add(event)
#         db.commit()
#         db.refresh(key)
        
#         return key
    
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Error extending key validity: {str(e)}")
#         raise ValueError(f"Error extending key validity: {str(e)}")

def update_checkout_date(serial_number, new_checkout_date, db):
    """
    Update the checkout date for a digital key and its associated reservation
    
    Parameters:
    serial_number (str): The key_uuid of the digital key to update
    new_checkout_date (datetime): The new checkout date
    db (Session): Database session
    
    Returns:
    dict: Updated pass data or None if key not found
    """
    try:
        # Find the digital key by key_uuid
        digital_key = db.query(DigitalKey).filter(
            DigitalKey.key_uuid == serial_number
        ).first()
        
        if not digital_key:
            logger.error(f"Digital key not found with serial number: {serial_number}")
            return None
        
        # Update the key's valid_until date
        digital_key.valid_until = new_checkout_date
        
        # Update the associated reservation's checkout date
        reservation = db.query(Reservation).filter(
            Reservation.id == digital_key.reservation_id
        ).first()
        
        if reservation:
            reservation.check_out = new_checkout_date
            logger.info(f"Updated reservation checkout date for reservation ID: {reservation.id}")
        else:
            logger.warning(f"Reservation not found for digital key: {serial_number}")
        
        # Update the key's timestamp to trigger update detection
        digital_key.updated_at = datetime.now(timezone.utc)
        
        # Commit changes to database
        db.add(digital_key)
        if reservation:
            db.add(reservation)
        db.commit()
        
        # Refresh the key to get updated data
        db.refresh(digital_key)
        
        # Get all necessary data for pass update
        room = None
        user = None
        
        if reservation:
            room = db.query(Room).filter(Room.id == reservation.room_id).first()
            user = db.query(User).filter(User.id == reservation.user_id).first()
        
        # Prepare pass data
        pass_data = {
            "key_uuid": digital_key.key_uuid,
            "room_number": room.room_number if room else "N/A",
            "guest_name": f"{user.first_name} {user.last_name}" if user else "Guest",
            "check_in": reservation.check_in.isoformat() if reservation else digital_key.valid_from.isoformat(),
            "check_out": reservation.check_out.isoformat() if reservation else digital_key.valid_until.isoformat(),
            "nfc_lock_id": room.nfc_lock_id if room else None,
            "is_active": digital_key.is_active
        }
        
        logger.info(f"Successfully updated checkout date for key: {serial_number}")
        return pass_data
        
    except Exception as e:
        logger.error(f"Error updating checkout date: {str(e)}")
        db.rollback()
        return None

def get_user_keys(db: Session, user_id: str) -> List[DigitalKey]:
    """
    Get all digital keys for a user
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        List of DigitalKey objects
    """
    try:
        # Get active reservations for the user
        reservations = db.query(Reservation).filter(
            Reservation.user_id == user_id,
            Reservation.status.in_([ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN])
        ).all()
        
        # Get keys for those reservations
        keys = []
        for reservation in reservations:
            reservation_keys = db.query(DigitalKey).filter(
                DigitalKey.reservation_id == reservation.id
            ).all()
            keys.extend(reservation_keys)
        
        return keys
    
    except Exception as e:
        logger.error(f"Error getting user keys: {str(e)}")
        return []


def get_active_keys(db: Session, user_id: Optional[str] = None) -> List[DigitalKey]:
    """
    Get all active keys, optionally filtered by user
    
    Args:
        db: Database session
        user_id: Optional User ID to filter
    
    Returns:
        List of active DigitalKey objects
    """
    try:
        # Base query for active keys
        query = db.query(DigitalKey).filter(
            DigitalKey.is_active == True,
            DigitalKey.status.in_([KeyStatus.CREATED, KeyStatus.ACTIVE]),
            DigitalKey.valid_until >= datetime.now(timezone.utc)
        )
        
        # Filter by user if provided
        if user_id:
            query = query.join(Reservation).filter(Reservation.user_id == user_id)
        
        return query.all()
    
    except Exception as e:
        logger.error(f"Error getting active keys: {str(e)}")
        return []


# def regenerate_key(db: Session, key_id: str) -> Tuple[DigitalKey, str]:
#     """
#     Regenerate a digital key (create a new one based on existing)
    
#     Args:
#         db: Database session
#         key_id: Existing key ID
    
#     Returns:
#         Tuple of (DigitalKey object, pass_url)
    
#     Raises:
#         ValueError: If key not found or issues with creating a new key
#     """
#     try:
#         # Get existing key
#         old_key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
#         if not old_key:
#             raise ValueError("Digital key not found")
        
#         # Deactivate old key
#         old_key.is_active = False
#         old_key.status = KeyStatus.REVOKED
#         db.add(old_key)
        
#         # Log deactivation
#         event = KeyEvent(
#             key_id=old_key.id,
#             event_type="key_regenerated",
#             timestamp=datetime.now(timezone.utc),
#             status="success"
#         )
#         db.add(event)
        
#         # Create new key based on same reservation
#         new_key, pass_url = create_digital_key(
#             db=db,
#             reservation_id=old_key.reservation_id,
#             pass_type=old_key.pass_type
#         )
        
#         return new_key, pass_url
    
#     except Exception as e:
#         db.rollback()
#         logger.error(f"Error regenerating key: {str(e)}")
#         raise ValueError(f"Error regenerating key: {str(e)}")


def get_expired_keys(db: Session) -> List[DigitalKey]:
    """
    Get all expired but still active keys
    
    Args:
        db: Database session
    
    Returns:
        List of expired DigitalKey objects
    """
    try:
        now = datetime.now(timezone.utc)
        
        # Find keys that are past validity but still active
        expired_keys = db.query(DigitalKey).filter(
            DigitalKey.is_active == True,
            DigitalKey.valid_until < now
        ).all()
        
        return expired_keys
    
    except Exception as e:
        logger.error(f"Error getting expired keys: {str(e)}")
        return []


def expire_outdated_keys(db: Session) -> int:
    """
    Automatically deactivate keys that are past their validity period
    
    Args:
        db: Database session
    
    Returns:
        Number of keys deactivated
    """
    try:
        expired_keys = get_expired_keys(db)
        count = 0
        
        for key in expired_keys:
            key.is_active = False
            key.status = KeyStatus.EXPIRED
            
            # Log expiration
            event = KeyEvent(
                key_id=key.id,
                event_type="key_expired",
                timestamp=datetime.now(timezone.utc),
                status="success"
            )
            
            db.add(key)
            db.add(event)
            count += 1
        
        db.commit()
        
        if count > 0:
            logger.info(f"Deactivated {count} expired keys")
            
        return count
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error expiring outdated keys: {str(e)}")
        return 0


def get_key_usage_history(db: Session, key_id: str) -> List[KeyEvent]:
    """
    Get usage history for a specific key
    
    Args:
        db: Database session
        key_id: Key ID
    
    Returns:
        List of KeyEvent objects
    """
    try:
        events = db.query(KeyEvent).filter(
            KeyEvent.key_id == key_id
        ).order_by(
            KeyEvent.timestamp.desc()
        ).all()
        
        return events
    
    except Exception as e:
        logger.error(f"Error getting key usage history: {str(e)}")
        return []


def get_key_details(db: Session, key_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a key including reservation and room
    
    Args:
        db: Database session
        key_id: Key ID
    
    Returns:
        Dictionary with key details
    """
    try:
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            raise ValueError("Digital key not found")
        
        # Get reservation
        reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
        if not reservation:
            raise ValueError("Reservation not found")
        
        # Get room
        room = db.query(Room).filter(Room.id == reservation.room_id).first()
        if not room:
            raise ValueError("Room not found")
        
        # Get user
        user = db.query(User).filter(User.id == reservation.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get hotel
        hotel = room.hotel
        
        # Compile the details
        details = {
            "key": {
                "id": key.id,
                "key_uuid": key.key_uuid,
                "pass_url": key.pass_url,
                "pass_type": key.pass_type,
                "valid_from": key.valid_from.isoformat(),
                "valid_until": key.valid_until.isoformat(),
                "is_active": key.is_active,
                "status": key.status,
                "activated_at": key.activated_at.isoformat() if key.activated_at else None,
                "last_used": key.last_used.isoformat() if key.last_used else None,
                "access_count": key.access_count,
                "created_at": key.created_at.isoformat()
            },
            "reservation": {
                "id": reservation.id,
                "confirmation_code": reservation.confirmation_code,
                "check_in": reservation.check_in.isoformat(),
                "check_out": reservation.check_out.isoformat(),
                "status": reservation.status
            },
            "room": {
                "id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "floor": room.floor
            },
            "user": {
                "id": user.id,
                "name": f"{user.first_name} {user.last_name}",
                "email": user.email
            },
            "hotel": {
                "id": hotel.id,
                "name": hotel.name,
                "address": hotel.address
            }
        }
        
        return details
    
    except Exception as e:
        logger.error(f"Error getting key details: {str(e)}")
        raise ValueError(f"Error getting key details: {str(e)}")
