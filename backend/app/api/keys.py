# backend/app/api/keys.py
from typing import Any, List, Tuple, Optional
from fastapi import Query, Body
import uuid
import logging
from datetime import datetime, timezone
from pydantic import BaseModel

from app.services.wallet_service import create_wallet_pass, settings
from app.services.key_service import update_checkout_date, activate_key, deactivate_key
from app.services.wallet_push_service import send_push_notifications, send_push_notifications_production
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.security import get_current_user, get_current_active_staff
from app.models.user import User, UserRole
from app.models.digital_key import DigitalKey, KeyStatus
from app.models.key_event import KeyEvent
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
from app.utils.date_formatting import format_datetime
from app.services.sms_service import validate_phone_number, send_sms
from app.schemas.sms import SMSResponseModel
from app.services.hotel_service import get_hotel_name

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# TODO remove class form here
class SendEmailRequest(BaseModel):
    alternative_email: Optional[str] = None
# Add this to your backend/app/api/keys.py file

# TODO: move it to key_service.py
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
            details=f"Created {key_in.pass_type.value} pass for room {room.room_number}, valid {digital_key.valid_from} to {digital_key.valid_until}",
            timestamp=datetime.now(timezone.utc)
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
            details=f"Error creating pass: {str(e)}",
            timestamp=datetime.now(timezone.utc)
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
                details=f"Email scheduled to be sent to {user.email}",
                timestamp=datetime.now(timezone.utc)
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
                details=f"Failed to schedule email: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(key_event)
            db.commit()
    # Send SMS if requested
    if hasattr(key_in, 'send_sms') and key_in.send_sms and hasattr(key_in, 'phone_numbers') and key_in.phone_numbers:
        valid_numbers = []
        
        # Validate phone numbers
        for phone in key_in.phone_numbers:
            if validate_phone_number(phone):
                valid_numbers.append(phone)
        
        if valid_numbers:
            # Create SMS content
            hotel_name = room.hotel.name if room and hasattr(room, 'hotel') and room.hotel else get_hotel_name(db, room.hotel_id)
            sms_content = (
                f"Your digital key for {hotel_name} is ready. "
                f"Room: {room.room_number}, "
                f"Check-in: {format_datetime(reservation.check_in)}, "
                f"Key URL: {pass_url}"
            )
            
            # Send SMS to each valid number
            success_count = 0
            failed_numbers = []
            
            for phone in valid_numbers:
                try:
                    # Instead of using background_tasks, send SMS synchronously
                    success, message = send_sms(phone, sms_content)
                    
                    if success:
                        # Log successful SMS sending
                        key_event = KeyEvent(
                            key_id=digital_key.id,
                            event_type="key_sms_sent",
                            device_info=f"API request by {current_user.email}",
                            status="success",
                            details=f"SMS sent to {phone} for {key_in.pass_type.value} pass",
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(key_event)
                        success_count += 1
                    else:
                        # Log SMS failure with the error message
                        failed_numbers.append(phone)
                        event = KeyEvent(
                            key_id=digital_key.id,
                            event_type="key_sms_failed",
                            device_info=f"API request by {current_user.email}",
                            status="error", 
                            details=f"Failed to send SMS to {phone}: {message}",
                            timestamp=datetime.now(timezone.utc)
                        )
                        db.add(event)
                    
                except Exception as e:
                    logger.error(f"Failed to send SMS to {phone}: {str(e)}")
                    failed_numbers.append(phone)
                    
                    # Log SMS failure
                    event = KeyEvent(
                        key_id=digital_key.id,
                        event_type="key_sms_failed",
                        device_info=f"API request by {current_user.email}",
                        status="error", 
                        details=f"Failed to send SMS to {phone}: {str(e)}",
                        timestamp=datetime.now(timezone.utc)
                    )
                    db.add(event)

            db.commit()
            
            # Prepare response
            if success_count == len(valid_numbers):
                return {
                    "message": f"SMS with digital key successfully sent to {success_count} phone number(s)",
                    "invalid_numbers": failed_numbers if failed_numbers else None
                }
            elif success_count > 0:
                return {
                    "message": f"SMS partially sent. Succeeded: {success_count}, Failed: {len(failed_numbers)}",
                    "failed_numbers": failed_numbers,
                    "invalid_numbers": failed_numbers if failed_numbers else None
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to send SMS to any number. Please try again later."
                )

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
    query = db.query(DigitalKey).options(
        joinedload(DigitalKey.reservation).joinedload(Reservation.user)
    )
    
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
    if current_user.role not in [UserRole.ADMIN, UserRole.HOTEL_STAFF]:
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
        details=f"Updated key status to {key_in.status}",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()
    
    return key


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
    
    # Get the reservation to check check-in date
    reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found for this key"
        )
    
    # Ensure both dates are timezone-aware
    check_in = reservation.check_in
    new_end_date = extension.new_end_date
    
    if check_in.tzinfo is None:
        check_in = check_in.replace(tzinfo=timezone.utc)
    
    if new_end_date.tzinfo is None:
        new_end_date = new_end_date.replace(tzinfo=timezone.utc)
    
    # Validate that new_end_date is after check_in
    if new_end_date <= check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date must be after check-in date"
        )
    
    # Save original date for logging
    original_valid_until = key.valid_until
    
    # Update key validity
    key.valid_until = new_end_date
    
    # Also update the reservation check-out date
    reservation.check_out = new_end_date
    
    # IMPORTANT: Update the key's updated_at timestamp for Apple Wallet change detection
    current_time = datetime.now(timezone.utc)
    key.updated_at = current_time
    
    # Make sure to save these changes to the database
    db.add(key)
    db.add(reservation)
    db.commit()
    db.refresh(key)
    
    try:
        # Use update_checkout_date from key_service instead of manual updates
        # This function handles all the necessary updates consistently
        pass_data = update_checkout_date(key.key_uuid, new_end_date, db)
        
        if pass_data:
            # Create a new wallet pass with updated data - pass the db session
            create_wallet_pass(pass_data, key.pass_type, db)
            
            # Send push notification to update the pass on user's device
            background_tasks.add_task(
                send_push_notifications_production,
                settings.APPLE_PASS_TYPE_ID,
                key.key_uuid
            )
        else:
            logger.error(f"Failed to update pass data for key: {key_id}")
    
    except Exception as e:
        logger.error(f"Error updating pass: {str(e)}")

    # Log key extension event
    event = KeyEvent(
        key_id=key.id,
        event_type="key_extended",
        device_info=f"API request by {current_user.email}",
        status="success",
        details=f"Extended from {original_valid_until} until: {key.valid_until}",
        timestamp=current_time
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
def activate_key_endpoint(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks
) -> Any:
    """
    Activate a digital key
    
    Staff can activate any key, but guests can only activate their own keys
    """
    # Check permissions for non-staff users
    if current_user.role not in [UserRole.ADMIN, UserRole.HOTEL_STAFF]:
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digital key not found"
            )
        
        reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
        if not reservation or reservation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    try:
        # Use the service function instead of duplicating logic
        key = activate_key(db, key_id)
        
        # Add additional information to event log
        event = KeyEvent(
            key_id=key.id,
            event_type="key_activated",
            device_info=f"API request by {current_user.email}",
            status="success",
            details=f"Key activated by {current_user.first_name} {current_user.last_name}",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(event)
        db.commit()
        
        # Update the wallet pass status immediately (not in background)
        # This ensures the wallet receives the update right away
        try:
            update_wallet_pass_status(db, key.id, is_active=True)
            logger.info(f"Wallet pass updated for key {key_id} to active state")
        except Exception as wallet_error:
            logger.error(f"Error updating wallet pass: {str(wallet_error)}")
            # Don't fail the activation if wallet update fails
            # Record the error
            error_event = KeyEvent(
                key_id=key.id,
                event_type="wallet_update_failed",
                device_info=f"API request by {current_user.email}",
                status="error",
                details=f"Failed to update wallet: {str(wallet_error)}",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(error_event)
            db.commit()
        
        return key
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# TODO: CHECK: these updates can sometimes be slow or if the wallet service occasionally has latency issues, 
# moving to a background task would be better.
@router.patch("/{key_id}/deactivate", response_model=DigitalKeySchema)
def deactivate_key_endpoint(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    current_user: User = Depends(get_current_active_staff),
    background_tasks: BackgroundTasks
) -> Any:
    """
    Deactivate a digital key (staff only)
    """
    try:
        # Use the service function instead of duplicating logic
        key = deactivate_key(db, key_id)
        
        # Add additional information to event log
        event = KeyEvent(
            key_id=key.id,
            event_type="key_deactivated",
            device_info=f"API request by {current_user.email}",
            status="success",
            details=f"Key deactivated by {current_user.first_name} {current_user.last_name}",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(event)
        db.commit()
        
        # Update the wallet pass status immediately (not in background)
        # This ensures the wallet receives the update right away
        try:
            update_wallet_pass_status(db, key.id, is_active=False)
            logger.info(f"Wallet pass updated for key {key_id} to inactive state")
        except Exception as wallet_error:
            logger.error(f"Error updating wallet pass: {str(wallet_error)}")
            # Don't fail the deactivation if wallet update fails
            # Record the error
            error_event = KeyEvent(
                key_id=key.id,
                event_type="wallet_update_failed",
                device_info=f"API request by {current_user.email}",
                status="error",
                details=f"Failed to update wallet: {str(wallet_error)}",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(error_event)
            db.commit()
        
        return key
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{key_id}/send-email", status_code=status.HTTP_200_OK)
def send_key_email_endpoint(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    request: SendEmailRequest = Body(default=None)
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
    if current_user.role not in [UserRole.ADMIN, UserRole.HOTEL_STAFF]:
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
        "hotel_name": room.hotel.name if room.hotel else settings.HOTEL_NAME,
        "room_number": room.room_number,
        "guest_name": f"{user.first_name} {user.last_name}",
        "check_in": reservation.check_in.isoformat(),
        "check_out": reservation.check_out.isoformat(),
        "nfc_lock_id": room.nfc_lock_id
    }
    
    # Determine which email to use
    email_to_use = user.email
    
    # If alternative email is provided and the user has permissions, use it
    if request and request.alternative_email and current_user.role in [UserRole.ADMIN, UserRole.HOTEL_STAFF]:
        # Validate the alternative email
        is_valid, validation_message = validate_email(request.alternative_email)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid alternative email: {validation_message}"
            )
        email_to_use = request.alternative_email
    else:
        # Check if the default email is valid
        is_valid, validation_message = validate_email(email_to_use)
        if not is_valid:
            # Create more detailed error message
            error_detail = f"Cannot send email to {email_to_use}: {validation_message}. Please verify the email address is correct and active, or provide an alternative email."
            logger.error(f"Email validation failed: {error_detail}")
            
            # Log the email validation failure
            event = KeyEvent(
                key_id=key.id,
                event_type="key_email_failed",
                device_info=f"API request by {current_user.email}",
                status="error",
                details=f"Invalid email: {email_to_use}. {validation_message}",
                timestamp=datetime.now(timezone.utc)
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
        email_to_use,
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
        details=f"Email sent to {email_to_use} for {key.pass_type.value} pass",
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()
    
    return {"message": f"Email with digital key successfully sent to {email_to_use}"}


@router.post("/{key_id}/send-sms", status_code=status.HTTP_200_OK, response_model=SMSResponseModel)
def send_key_sms_endpoint(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    phone_numbers: List[str],  # Accept list of phone numbers
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send SMS with digital key pass to the user
    """
    # Get the digital key
    key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital key not found. Please verify the key ID and try again."
        )

    # Check permissions for non-staff users
    if current_user.role not in [UserRole.ADMIN, UserRole.HOTEL_STAFF]:
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
            detail="Reservation not found for this key."
        )
    
    # Get the room for this reservation
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found for this reservation."
        )
    
    # Validate phone numbers
    valid_numbers = []
    invalid_numbers = []
    
    for phone in phone_numbers:
        if validate_phone_number(phone):
            valid_numbers.append(phone)
        else:
            invalid_numbers.append(phone)
    
    if not valid_numbers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No valid phone numbers provided. Invalid numbers: {', '.join(invalid_numbers)}"
        )
    
    # Create SMS content
    hotel_name = room.hotel.name if room and hasattr(room, 'hotel') and room.hotel else get_hotel_name(db, room.hotel_id)
    sms_content = (
        f"Your digital key for {hotel_name} is ready. "
        f"Room: {room.room_number}, "
        f"Check-in: {format_datetime(reservation.check_in)}, "
        f"Key URL: {key.pass_url}"
    )

    # Send SMS to each valid number
    success_count = 0
    failed_numbers = []
    
    for phone in valid_numbers:
        try:
            # Instead of using background_tasks, send SMS synchronously
            success, message = send_sms(phone, sms_content)
            
            if success:
                # Log successful SMS sending
                key_event = KeyEvent(
                    key_id=key.id,
                    event_type="key_sms_sent",
                    device_info=f"API request by {current_user.email}",
                    status="success",
                    details=f"SMS sent to {phone} for {key.pass_type.value} pass",
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(key_event)
                success_count += 1
            else:
                # Log SMS failure with the error message
                failed_numbers.append(phone)
                event = KeyEvent(
                    key_id=key.id,
                    event_type="key_sms_failed",
                    device_info=f"API request by {current_user.email}",
                    status="error", 
                    details=f"Failed to send SMS to {phone}: {message}",
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(event)
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {str(e)}")
            failed_numbers.append(phone)
            
            # Log SMS failure
            event = KeyEvent(
                key_id=key.id,
                event_type="key_sms_failed",
                device_info=f"API request by {current_user.email}",
                status="error", 
                details=f"Failed to send SMS to {phone}: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(event)

    db.commit()
    
    # Prepare response
    if success_count == len(valid_numbers):
        return {
            "message": f"SMS with digital key successfully sent to {success_count} phone number(s)",
            "invalid_numbers": invalid_numbers if invalid_numbers else None
        }
    elif success_count > 0:
        return {
            "message": f"SMS partially sent. Succeeded: {success_count}, Failed: {len(failed_numbers)}",
            "failed_numbers": failed_numbers,
            "invalid_numbers": invalid_numbers if invalid_numbers else None
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS to any number. Please try again later."
        )


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
