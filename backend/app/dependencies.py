# backend/app/dependencies.py
from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security import get_current_user, get_current_active_staff, get_current_active_admin
from app.models.user import User
from app.models.hotel import Hotel
from app.models.reservation import Reservation


def get_current_user_hotel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_staff)
) -> Hotel:
    """
    Get the hotel associated with the current staff user
    """
    # Get staff-hotel association
    staff = db.query(User).filter(
        User.id == current_user.id,
        User.role.in_(["admin", "hotel_staff"])
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not hotel staff"
        )
    
    # In a multi-hotel system, you would get the specific hotel
    # For this implementation, we'll just get the first hotel
    hotel = db.query(Hotel).first()
    
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hotel found"
        )
    
    return hotel


def get_reservation_or_404(
    reservation_id: str,
    db: Session = Depends(get_db)
) -> Reservation:
    """
    Get a reservation by ID or raise 404
    """
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    return reservation


def check_reservation_permissions(
    reservation: Reservation = Depends(get_reservation_or_404),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Reservation:
    """
    Check if current user has permission to access this reservation
    
    Staff can access any reservation, but guests can only access their own
    """
    if current_user.role in ["admin", "hotel_staff"]:
        return reservation
    
    if reservation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this reservation"
        )
    
    return reservation
