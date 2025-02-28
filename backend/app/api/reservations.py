# backend/app/api/reservations.py
from typing import Any, List
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.session import get_db
from app.security import get_current_user, get_current_active_staff
from app.dependencies import check_reservation_permissions
from app.models.user import User
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import Room
from app.schemas.reservation import (
    Reservation as ReservationSchema,
    ReservationCreate,
    ReservationUpdate
)

router = APIRouter()


@router.post("", response_model=ReservationSchema, status_code=status.HTTP_201_CREATED)
def create_reservation(
    *,
    db: Session = Depends(get_db),
    reservation_in: ReservationCreate,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Create a new reservation (staff only)
    """
    # Check if user exists
    user = db.query(User).filter(User.id == reservation_in.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if room exists
    room = db.query(Room).filter(Room.id == reservation_in.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check room availability for this period
    overlapping = db.query(Reservation).filter(
        Reservation.room_id == reservation_in.room_id,
        Reservation.status.in_(["confirmed", "checked_in"]),
        Reservation.check_out > reservation_in.check_in,
        Reservation.check_in < reservation_in.check_out
    ).first()
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room is already reserved for this period"
        )
    
    # Generate confirmation code
    confirmation_code = f"RES{uuid.uuid4().hex[:8].upper()}"
    
    # Create reservation
    reservation = Reservation(
        user_id=reservation_in.user_id,
        room_id=reservation_in.room_id,
        confirmation_code=confirmation_code,
        check_in=reservation_in.check_in,
        check_out=reservation_in.check_out,
        status=ReservationStatus.CONFIRMED,
        number_of_guests=reservation_in.number_of_guests,
        special_requests=reservation_in.special_requests
    )
    
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    
    return reservation


@router.get("", response_model=List[ReservationSchema])
def read_reservations(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    status: List[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve reservations
    
    Staff can see all reservations, guests can only see their own
    """
    query = db.query(Reservation)
    
    # Filter by status if provided
    if status:
        query = query.filter(Reservation.status.in_(status))
    
    # For non-staff users, only show their own reservations
    if current_user.role not in ["admin", "hotel_staff"]:
        query = query.filter(Reservation.user_id == current_user.id)
    
    # Order by check-in date (soonest first)
    query = query.order_by(Reservation.check_in.desc())
    
    reservations = query.offset(skip).limit(limit).all()
    return reservations


@router.get("/active", response_model=List[ReservationSchema])
def read_active_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve currently active reservations (checked-in or upcoming)
    
    Staff can see all active reservations, guests can only see their own
    """
    now = datetime.utcnow()
    
    query = db.query(Reservation).filter(
        Reservation.status.in_(["confirmed", "checked_in"]),
        Reservation.check_out >= now
    )
    
    # For non-staff users, only show their own reservations
    if current_user.role not in ["admin", "hotel_staff"]:
        query = query.filter(Reservation.user_id == current_user.id)
    
    # Order by check-in date (soonest first)
    query = query.order_by(Reservation.check_in)
    
    reservations = query.all()
    return reservations


@router.get("/{reservation_id}", response_model=ReservationSchema)
def read_reservation(
    *,
    reservation: Reservation = Depends(check_reservation_permissions)
) -> Any:
    """
    Get a specific reservation by ID
    
    Staff can access any reservation, guests can only access their own
    """
    return reservation


@router.patch("/{reservation_id}", response_model=ReservationSchema)
def update_reservation(
    *,
    db: Session = Depends(get_db),
    reservation_id: str,
    reservation_in: ReservationUpdate,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Update a reservation (staff only)
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Check if check-out date is being extended
    if reservation_in.check_out and reservation_in.check_out > reservation.check_out:
        # Check room availability for extended period
        overlapping = db.query(Reservation).filter(
            Reservation.room_id == reservation.room_id,
            Reservation.id != reservation_id,
            Reservation.status.in_(["confirmed", "checked_in"]),
            Reservation.check_in < reservation_in.check_out,
            Reservation.check_out > reservation.check_out
        ).first()
        
        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot extend reservation - room is already booked"
            )
    
    # Update reservation data
    for field, value in reservation_in.model_dump(exclude_unset=True).items():
        setattr(reservation, field, value)
    
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    
    return reservation


@router.patch("/{reservation_id}/check-in", response_model=ReservationSchema)
def check_in_reservation(
    *,
    db: Session = Depends(get_db),
    reservation_id: str,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Mark a reservation as checked in (staff only)
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    if reservation.status != ReservationStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in reservation with status: {reservation.status}"
        )
    
    reservation.status = ReservationStatus.CHECKED_IN
    
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    
    return reservation


@router.patch("/{reservation_id}/check-out", response_model=ReservationSchema)
def check_out_reservation(
    *,
    db: Session = Depends(get_db),
    reservation_id: str,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Mark a reservation as checked out (staff only)
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    if reservation.status != ReservationStatus.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check out reservation with status: {reservation.status}"
        )
    
    reservation.status = ReservationStatus.CHECKED_OUT
    
    # Deactivate any active keys for this reservation
    for key in reservation.digital_keys:
        if key.is_active:
            key.is_active = False
            key.status = "expired"
            db.add(key)
    
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    
    return reservation


@router.delete("/{reservation_id}", response_model=ReservationSchema)
def cancel_reservation(
    *,
    db: Session = Depends(get_db),
    reservation_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Cancel a reservation
    
    Staff can cancel any reservation, guests can only cancel their own
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    # Check permissions for non-staff users
    if current_user.role not in ["admin", "hotel_staff"] and reservation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if reservation.status in [ReservationStatus.CHECKED_OUT, ReservationStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel reservation with status: {reservation.status}"
        )
    
    reservation.status = ReservationStatus.CANCELLED
    
    # Deactivate any active keys for this reservation
    for key in reservation.digital_keys:
        if key.is_active:
            key.is_active = False
            key.status = "revoked"
            db.add(key)
    
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    
    return reservation
