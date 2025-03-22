# backend/app/api/keys.py
from typing import Any, List, Tuple, Optional
from fastapi import Query
import uuid
import logging
from datetime import datetime, timezone

from app.services.wallet_service import create_wallet_pass, settings
from app.services.key_service import update_checkout_date
from app.services.wallet_push_service import send_push_notifications, send_push_notifications_production
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security import get_current_user, get_current_active_staff
from app.models.user import User
from app.models.digital_key import DigitalKey, KeyStatus, KeyEvent
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from app.schemas.digital_key import (
    DigitalKey as DigitalKeySchema,
    DigitalKeyCreate,
    DigitalKeyUpdate,
    KeyExtension,
    KeyEvent as KeyEventSchema
)
from app.services.email_service import send_key_email, validate_email
from app.services.pass_update_service import update_wallet_pass_status

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=DigitalKeySchema, status_code=status.HTTP_201_CREATED)
def create_digital_key(
    *,
    db: Session = Depends(get_db),
    key_in: DigitalKeyCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Create a new digital key for a reservation
    """
    # Check if reservation exists
    reservation = db.query(Reservation).filter(Reservation.id == key_in.reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found. Please verify the reservation ID and try again."
        )
    
    # Verify reservation status
    if reservation.status not in [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create key for reservation with status: {reservation.status}. Keys can only be created for confirmed or checked-in reservations."
        )
    
    # Get user and room info
    user = db.query(User).filter(User.id == reservation.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found for this reservation. The user account may have been deleted or the reservation is misconfigured."
        )
    
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found for this reservation. The room may have been deleted or the reservation is misconfigured."
        )
    
    # If email will be sent, validate the email first
    if key_in.send_email:
        is_valid, validation_message = validate_email(user.email)
        if not is_valid:
            error_detail = f"Cannot create key with email option: {user.email} is invalid. {validation_message}. Please update the user's email address before creating a key with the email option."
            
            # Log the validation failure
            logger.error(f"Email validation failed: {error_detail}")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )
    
    # Generate unique key UUID
    key_uuid = str(uuid.uuid4())

    # IMPORTANT: First create the digital key in the database
    digital_key = DigitalKey(
        reservation_id=key_in.reservation_id,
        key_uuid=key_uuid,
        pass_url=None,  # Will be updated after pass creation
        pass_type=key_in.pass_type,
        valid_from=reservation.check_in,
        valid_until=reservation.check_out,
        is_active=True,
        status=KeyStatus.CREATED,
        auth_token=key_uuid  # Set auth_token initially to the same as key_uuid
    )
    
    db.add(digital_key)
    db.commit()
    db.refresh(digital_key)

    # Create pass data for wallet pass
    pass_data = {
        "key_uuid": key_uuid,
        "hotel_name": room.hotel.name,
        "room_number": room.room_number,
        "guest_name": f"{user.first_name} {user.last_name}",
        "check_in": reservation.check_in.isoformat(),
        "check_out": reservation.check_out.isoformat(),
        "nfc_lock_id": room.nfc_lock_id
    }

    # Create wallet pass with the database session
    try:
        pass_url = create_wallet_pass(pass_data, key_in.pass_type, db)
        
        # Update the pass_url
        digital_key.pass_url = pass_url
        db.commit()
        # Create key creation event
        key_event = KeyEvent(
            key_id=digital_key.id,
            event_type="key_created",
            device_info=f"API request by {current_user.email}",
            status="success",
            details=f"Created {key_in.pass_type.value} pass for room {room.room_number}, valid {digital_key.valid_from} to {digital_key.valid_until}"
        )
        db.add(key_event)
        db.commit()

    except Exception as e:
        # Log the error
        key_event = KeyEvent(
            key_id=digital_key.id,
            event_type="key_creation_failed",
            device_info=f"API request by {current_user.email}",
            status="error",
            details=f"Error creating pass: {str(e)}"
        )
        db.add(key_event)
        db.commit()

        # Clean up the digital key if pass creation fails
        db.delete(digital_key)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating wallet pass: {str(e)}. Please try again or contact support if this error persists."
        )
    
    # Send email in background if requested
    if key_in.send_email:
        logger.info(f"Adding email task for digital key {digital_key.id} to {user.email}")
        try:
            background_tasks.add_task(
                send_key_email,
                user.email,
                f"{user.first_name} {user.last_name}",
                pass_url,
                digital_key.id,
                pass_data
            )
            
            # Log email scheduling
            key_event = KeyEvent(
                key_id=digital_key.id,
                event_type="key_email_scheduled",
                device_info=f"API request by {current_user.email}",
                status="success",
                details=f"Email scheduled to be sent to {user.email}"
            )
            db.add(key_event)
            db.commit()
            
        except Exception as e:
            # Log email scheduling failure but don't fail the key creation
            logger.error(f"Failed to schedule email: {str(e)}")
            key_event = KeyEvent(
                key_id=digital_key.id,
                event_type="key_email_scheduling_failed",
                device_info=f"API request by {current_user.email}",
                status="error",
                details=f"Failed to schedule email: {str(e)}"
            )
            db.add(key_event)
            db.commit()

    return digital_key


@router.get("", response_model=List[DigitalKeySchema])
def read_keys(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    reservation_id: str = None,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Retrieve digital keys, filtered by reservation if provided
    """
    query = db.query(DigitalKey)
    
    if reservation_id:
        query = query.filter(DigitalKey.reservation_id == reservation_id)
    
    keys = query.offset(skip).limit(limit).all()
    return keys


@router.get("/{key_id}", response_model=DigitalKeySchema)
def read_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific digital key by ID
    
    Staff can access any key, but guests can only access their own keys
    """
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found"
        )
    
    # Check permissions for non-staff users
    if current_user.role not in ["admin", "hotel_staff"]:
        reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
        if not reservation or reservation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return key


@router.patch("/{key_id}", response_model=DigitalKeySchema)
def update_key(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    key_in: DigitalKeyUpdate,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Update a digital key
    """
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found"
        )
    
    # Update key data
    for field, value in key_in.model_dump(exclude_unset=True).items():
        setattr(key, field, value)
    
    db.add(key)
    db.commit()
    db.refresh(key)
    
    # Log key update event
    event = KeyEvent(
        key_id=key.id,
        event_type="key_updated",
        device_info=f"API request by {current_user.email}",
        status="success",
        details=f"Status: {key.status}, Active: {key.is_active}"
    )
    db.add(event)
    db.commit()
    
    return key


# TODO: add validation for extend_key validity, checkout could not be < checkin date, like reservation i think
@router.patch("/{key_id}/extend", response_model=DigitalKeySchema)
def extend_key_validity(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    extension: KeyExtension,
    current_user: User = Depends(get_current_active_staff),
    background_tasks: BackgroundTasks
):
    """
    Extend the validity period of a digital key
    """
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found"
        )
    
    # Update key validity
    key.valid_until = extension.new_end_date
    
    # Also update the reservation check-out date
    reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
    if reservation:
        reservation.check_out = extension.new_end_date
    
    db.add(key)
    db.commit()
    db.refresh(key)
    
    try:
        # Get all necessary data
        room = db.query(Room).filter(Room.id == reservation.room_id).first()
        user = db.query(User).filter(User.id == reservation.user_id).first()

        pass_data = {
            "key_uuid": key.key_uuid,
            "room_number": room.room_number,
            "guest_name": f"{user.first_name} {user.last_name}",
            "check_in": reservation.check_in.isoformat(),
            "check_out": reservation.check_out.isoformat(),  # Updated checkout date
            "nfc_lock_id": room.nfc_lock_id,
            "is_active": key.is_active
        }
        
        # Use the existing function
        create_wallet_pass(pass_data, key.pass_type)
        
        # Send push notification
        background_tasks.add_task(
            send_push_notifications_production,
            settings.APPLE_PASS_TYPE_ID,
            key.key_uuid
        )
    
    except Exception as e:
        logger.error(f"Error updating pass: {str(e)}")

    # Log key extension event
    event = KeyEvent(
        key_id=key.id,
        event_type="key_extended",
        device_info=f"API request by {current_user.email}",
        status="success",
        details=f"Extended until: {key.valid_until}"
    )
    db.add(event)
    db.commit()
    
    return key

# @router.get("/{pass_type_id}")
# async def get_changed_passes(
#     pass_type_id: str,
#     passesUpdatedSince: Optional[str] = Query(None),
#     db: Session = Depends(get_db)
# ):
#     """Return serial numbers of passes that have changed since a timestamp"""
#     logger.info(f"What changed request for pass type: {pass_type_id}, since: {passesUpdatedSince}")
    
#     # Parse the timestamp if provided
#     update_since = None
#     if passesUpdatedSince:
#         try:
#             update_since = datetime.strptime(passesUpdatedSince, "%Y-%m-%dT%H:%M:%SZ")
#             update_since = update_since.replace(tzinfo=timezone.utc)
#         except ValueError:
#             logger.warning(f"Invalid timestamp format: {passesUpdatedSince}")
    
#     # Query for updated passes
#     query = db.query(DigitalKey).filter(
#         DigitalKey.pass_type == KeyType.APPLE
#     )
    
#     if update_since:
#         query = query.filter(DigitalKey.updated_at > update_since)
    
#     # Get the serial numbers
#     serial_numbers = [key.key_uuid for key in query.all()]
    
#     # Get current timestamp for lastUpdated
#     last_updated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
#     # Return both serialNumbers and lastUpdated
#     return {
#         "serialNumbers": serial_numbers,
#         "lastUpdated": last_updated
#     }


@router.patch("/{key_id}/activate", response_model=DigitalKeySchema)
def activate_key(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks  # Add this parameter
) -> Any:
    """
    Activate a digital key
    
    Staff can activate any key, but guests can only activate their own keys
    """
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found"
        )
    
    # Check permissions for non-staff users
    if current_user.role not in ["admin", "hotel_staff"]:
        reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
        if not reservation or reservation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    # Activate the key
    key.is_active = True
    key.status = KeyStatus.ACTIVE
    key.activated_at = datetime.now(timezone.utc)
    
    db.add(key)
    db.commit()
    db.refresh(key)
    
    # Log key activation event
    event = KeyEvent(
        key_id=key.id,
        event_type="key_activated",
        device_info=f"API request by {current_user.email}",
        status="success",
        details=f"Activated at: {key.activated_at}"
    )
    db.add(event)
    db.commit()
    
    # Add this: Update the pass in real-time
    background_tasks.add_task(
        update_wallet_pass_status,
        db,
        key.id,
        is_active=True
    )
    
    return key


@router.patch("/{key_id}/deactivate", response_model=DigitalKeySchema)
def deactivate_key(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    current_user: User = Depends(get_current_active_staff),
    background_tasks: BackgroundTasks  # Add this parameter
) -> Any:
    """
    Deactivate a digital key (staff only)
    """
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found"
        )
    
    # Deactivate the key
    key.is_active = False
    key.status = KeyStatus.REVOKED
    
    db.add(key)
    db.commit()
    db.refresh(key)
    
    # Log key deactivation event
    event = KeyEvent(
        key_id=key.id,
        event_type="key_deactivated",
        device_info=f"API request by {current_user.email}",
        status="success"
    )
    db.add(event)
    db.commit()
    
    # Add this: Update the pass in real-time
    background_tasks.add_task(
        update_wallet_pass_status,
        db,
        key.id,
        is_active=False
    )

    return key


# Add this to your backend/app/api/keys.py file

@router.post("/{key_id}/send-email", status_code=status.HTTP_200_OK)
def send_key_email_endpoint(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Send email with digital key pass to the user
    """
    # Get the digital key
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found. Please verify the key ID and try again."
        )

    # Check permissions for non-staff users
    if current_user.role not in ["admin", "hotel_staff"]:
        reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
        if not reservation or reservation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to send this key. Only admins, hotel staff, or the reservation owner can perform this action."
            )

    # Get reservation and user info
    reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found for this key. The reservation may have been deleted or the key is misconfigured."
        )
    
    user = db.query(User).filter(User.id == reservation.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found for this reservation. The user account may have been deleted or the reservation is misconfigured."
        )
    
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found for this reservation. The room may have been deleted or the reservation is misconfigured."
        )
    
    # Create pass data for email
    pass_data = {
        "key_uuid": key.key_uuid,
        "hotel_name": room.hotel.name if room.hotel else "Hotel",
        "room_number": room.room_number,
        "guest_name": f"{user.first_name} {user.last_name}",
        "check_in": reservation.check_in.isoformat(),
        "check_out": reservation.check_out.isoformat(),
        "nfc_lock_id": room.nfc_lock_id
    }
    
    # Check email validity before sending
    is_valid, validation_message = validate_email(user.email)
    if not is_valid:
        # Create more detailed error message
        error_detail = f"Cannot send email to {user.email}: {validation_message}. Please verify the email address is correct and active, or update the user's email to a valid address."
        logger.error(f"Email validation failed: {error_detail}")
        
        # Log the email validation failure
        event = KeyEvent(
            key_id=key.id,
            event_type="key_email_failed",
            device_info=f"API request by {current_user.email}",
            status="error",
            details=f"Invalid email: {user.email}. {validation_message}"
        )
        db.add(event)
        db.commit()
        
        # Return error to the frontend
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    
    # Send email in background
    background_tasks.add_task(
        send_key_email,
        user.email,
        f"{user.first_name} {user.last_name}",
        key.pass_url,
        key.id,
        pass_data
    )
    
    # Log the email send event
    event = KeyEvent(
        key_id=key.id,
        event_type="key_email_sent",
        device_info=f"API request by {current_user.email}",
        status="success",
        details=f"Email sent to {user.email} for {key.pass_type.value} pass"
    )
    db.add(event)
    db.commit()
    
    return {"message": f"Email with digital key successfully sent to {user.email}"}


@router.get("/{key_id}/events", response_model=List[KeyEventSchema])
def read_key_events(
    key_id: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Get all events for a specific key (staff only)
    """
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found"
        )
    
    events = db.query(KeyEvent).filter(
        KeyEvent.key_id == key_id
    ).order_by(
        KeyEvent.timestamp.desc()
    ).offset(skip).limit(limit).all()
    
    return events

# # TODO: add router and test it, copied from key_service
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

# TODO: maybe invoke functions in key_service that
# do not exists here to create endpoints, like get_key_details, get_key_usage_history etc