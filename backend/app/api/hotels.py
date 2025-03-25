# backend/app/api/hotels.py
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security import get_current_user, get_current_active_admin
from app.models.user import User
from app.models.hotel import Hotel
from app.schemas.hotel import (
    Hotel as HotelSchema,
    HotelCreate,
    HotelUpdate
)

router = APIRouter()


@router.post("", response_model=HotelSchema, status_code=status.HTTP_201_CREATED)
def create_hotel(
    *,
    db: Session = Depends(get_db),
    hotel_in: HotelCreate,
    current_user: User = Depends(get_current_active_admin)
) -> Any:
    """
    Create a new hotel (admin only)
    """
    hotel = Hotel(
        name=hotel_in.name,
        address=hotel_in.address,
        city=hotel_in.city,
        state=hotel_in.state,
        country=hotel_in.country,
        postal_code=hotel_in.postal_code,
        phone_number=hotel_in.phone_number,
        email=hotel_in.email,
        website=hotel_in.website,
        logo_url=hotel_in.logo_url,
        is_active=True
    )
    
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    
    return hotel


@router.get("", response_model=List[HotelSchema])
def read_hotels(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve hotels
    """
    hotels = db.query(Hotel).filter(Hotel.is_active == True).offset(skip).limit(limit).all()
    return hotels


@router.get("/{hotel_id}", response_model=HotelSchema)
def read_hotel(
    hotel_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific hotel by ID
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id, Hotel.is_active == True).first()
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
    return hotel


@router.put("/{hotel_id}", response_model=HotelSchema)
def update_hotel(
    *,
    db: Session = Depends(get_db),
    hotel_id: str,
    hotel_in: HotelUpdate,
    current_user: User = Depends(get_current_active_admin)
) -> Any:
    """
    Update a hotel (admin only)
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
    
    # Update hotel data
    for field, value in hotel_in.model_dump(exclude_unset=True).items():
        setattr(hotel, field, value)
    
    db.add(hotel)
    db.commit()
    db.refresh(hotel)

    return hotel


@router.delete("/{hotel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hotel(
    *,
    db: Session = Depends(get_db),
    hotel_id: str,
    current_user: User = Depends(get_current_active_admin)
):  # Remove the "-> Any" return type annotation
    """
    Deactivate a hotel (admin only)
    """
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
    
    # Instead of deleting, mark as inactive
    hotel.is_active = False
    
    db.add(hotel)
    db.commit()
    
    return None
