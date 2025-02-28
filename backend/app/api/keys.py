# backend/app/api/keys.py
from typing import Any, List
import uuid
from datetime import datetime

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
from app.services.email_service import send_key_email
from app.services.wallet_service import create_wallet_pass

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
            detail="Reservation not found"
        )
    
    # Verify reservation status
    if reservation.status not in [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create key for reservation with status: {reservation.status}"
        )
    
    # Get user and room info
    user = db.query(User).filter(User.id == reservation.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    room = db.query(Room).filter(Room.id == reservation.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Generate unique key UUID
    key_uuid = str(uuid.uuid4())
    
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
    
    # Create wallet pass
    try:
        pass_url = create_wallet_pass(pass_data, key_in.pass_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating wallet pass: {str(e)}"
        )
    
    # Create digital key record
    digital_key = DigitalKey(
        reservation_id=key_in.reservation_id,
        key_uuid=key_uuid,
        pass_url=pass_url,
        pass_type=key_in.pass_type,
        valid_from=reservation.check_in,
        valid_until=reservation.check_out,
        is_active=True,
        status=KeyStatus.CREATED
    )
    
    db.add(digital_key)
    db.commit()
    db.refresh(digital_key)
    
    # Send email in background if requested
    if key_in.send_email:
        background_tasks.add_task(
            send_key_email,
            user.email,
            f"{user.first_name} {user.last_name}",
            pass_url,
            digital_key.id,
            pass_data
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


@router.patch("/{key_id}/extend", response_model=DigitalKeySchema)
def extend_key_validity(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    extension: KeyExtension,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
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


@router.patch("/{key_id}/activate", response_model=DigitalKeySchema)
def activate_key(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    current_user: User = Depends(get_current_user)
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
    key.activated_at = datetime.utcnow()
    
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
    
    return key


@router.patch("/{key_id}/deactivate", response_model=DigitalKeySchema)
def deactivate_key(
    *,
    db: Session = Depends(get_db),
    key_id: str,
    current_user: User = Depends(get_current_active_staff)
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
    
    return key


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
