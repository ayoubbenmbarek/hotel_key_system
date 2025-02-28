# backend/app/api/rooms.py
from typing import Any, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.security import get_current_user, get_current_active_staff
from app.models.user import User
from app.models.room import Room, RoomType
from app.schemas.room import (
    Room as RoomSchema,
    RoomCreate,
    RoomUpdate
)

router = APIRouter()


@router.post("", response_model=RoomSchema, status_code=status.HTTP_201_CREATED)
def create_room(
    *,
    db: Session = Depends(get_db),
    room_in: RoomCreate,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Create a new room (staff only)
    """
    # Check if room number already exists for this hotel
    existing_room = db.query(Room).filter(
        Room.hotel_id == room_in.hotel_id,
        Room.room_number == room_in.room_number
    ).first()
    
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room with number {room_in.room_number} already exists in this hotel"
        )
    
    # Generate a unique NFC lock ID if not provided
    if not room_in.nfc_lock_id:
        room_in.nfc_lock_id = f"LOCK-{uuid.uuid4().hex[:8].upper()}"
    else:
        # Check if lock ID is already in use
        existing_lock = db.query(Room).filter(Room.nfc_lock_id == room_in.nfc_lock_id).first()
        if existing_lock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lock ID {room_in.nfc_lock_id} is already in use"
            )
    
    # Create room
    room = Room(
        hotel_id=room_in.hotel_id,
        room_number=room_in.room_number,
        floor=room_in.floor,
        room_type=room_in.room_type,
        max_occupancy=room_in.max_occupancy,
        nfc_lock_id=room_in.nfc_lock_id,
        is_active=True
    )
    
    db.add(room)
    db.commit()
    db.refresh(room)
    
    return room


@router.get("", response_model=List[RoomSchema])
def read_rooms(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    hotel_id: str = None,
    room_type: List[RoomType] = Query(None),
    is_active: bool = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve rooms, filtered by hotel, type, or status
    """
    query = db.query(Room)
    
    # Apply filters
    if hotel_id:
        query = query.filter(Room.hotel_id == hotel_id)
    
    if room_type:
        query = query.filter(Room.room_type.in_(room_type))
    
    if is_active is not None:
        query = query.filter(Room.is_active == is_active)
    
    # Order by room number
    query = query.order_by(Room.room_number)
    
    rooms = query.offset(skip).limit(limit).all()
    return rooms


@router.get("/available", response_model=List[RoomSchema])
def read_available_rooms(
    db: Session = Depends(get_db),
    hotel_id: str = Query(..., description="Hotel ID"),
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    room_type: List[RoomType] = Query(None),
    max_occupancy: int = Query(None),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Find available rooms for a given date range
    """
    # Convert string dates to datetime
    from datetime import datetime
    try:
        check_in_date = datetime.fromisoformat(check_in)
        check_out_date = datetime.fromisoformat(check_out)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD or YYYY-MM-DDThh:mm:ss"
        )
    
    # Check date range validity
    if check_in_date >= check_out_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-out date must be after check-in date"
        )
    
    # First, get all rooms matching the criteria
    query = db.query(Room).filter(Room.hotel_id == hotel_id, Room.is_active == True)
    
    if room_type:
        query = query.filter(Room.room_type.in_(room_type))
    
    if max_occupancy:
        query = query.filter(Room.max_occupancy >= max_occupancy)
    
    all_rooms = query.all()
    
    # Then, filter out rooms with overlapping reservations
    available_rooms = []
    
    for room in all_rooms:
        # Check if room has any overlapping reservations
        from app.models.reservation import Reservation
        
        overlapping = db.query(Reservation).filter(
            Reservation.room_id == room.id,
            Reservation.status.in_(["confirmed", "checked_in"]),
            Reservation.check_out > check_in_date,
            Reservation.check_in < check_out_date
        ).first()
        
        if not overlapping:
            available_rooms.append(room)
    
    return available_rooms


@router.get("/{room_id}", response_model=RoomSchema)
def read_room(
    room_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get a specific room by ID
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return room


@router.put("/{room_id}", response_model=RoomSchema)
def update_room(
    *,
    db: Session = Depends(get_db),
    room_id: str,
    room_in: RoomUpdate,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Update a room (staff only)
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # If changing room number, check if new number already exists
    if room_in.room_number and room_in.room_number != room.room_number:
        existing_room = db.query(Room).filter(
            Room.hotel_id == room.hotel_id,
            Room.room_number == room_in.room_number,
            Room.id != room_id
        ).first()
        
        if existing_room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Room with number {room_in.room_number} already exists in this hotel"
            )
    
    # If changing lock ID, check if new ID already exists
    if room_in.nfc_lock_id and room_in.nfc_lock_id != room.nfc_lock_id:
        existing_lock = db.query(Room).filter(
            Room.nfc_lock_id == room_in.nfc_lock_id,
            Room.id != room_id
        ).first()
        
        if existing_lock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lock ID {room_in.nfc_lock_id} is already in use"
            )
    
    # Update room data
    for field, value in room_in.model_dump(exclude_unset=True).items():
        setattr(room, field, value)
    
    db.add(room)
    db.commit()
    db.refresh(room)
    
    return room


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_room(
    *,
    db: Session = Depends(get_db),
    room_id: str,
    current_user: User = Depends(get_current_active_staff)
) -> Any:
    """
    Deactivate a room (staff only)
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Check if room has any upcoming reservations
    from app.models.reservation import Reservation
    from datetime import datetime
    
    upcoming = db.query(Reservation).filter(
        Reservation.room_id == room_id,
        Reservation.status.in_(["confirmed", "checked_in"]),
        Reservation.check_out > datetime.utcnow()
    ).first()
    
    if upcoming:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate room with upcoming or active reservations"
        )
    
    # Deactivate the room
    room.is_active = False
    
    db.add(room)
    db.commit()
    
    return None
