# backend/app/schemas/room.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.schemas.hotel import Hotel
from app.models.room import RoomType


# Shared properties
class RoomBase(BaseModel):
    hotel_id: str
    room_number: str
    floor: Optional[int] = None
    room_type: RoomType = RoomType.STANDARD
    max_occupancy: Optional[int] = 2
    nfc_lock_id: Optional[str] = None


# Properties to receive on room creation
class RoomCreate(RoomBase):
    pass


# Properties to receive on room update
class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    floor: Optional[int] = None
    room_type: Optional[RoomType] = None
    max_occupancy: Optional[int] = None
    nfc_lock_id: Optional[str] = None
    is_active: Optional[bool] = None


# Properties shared by models returned from API
class Room(RoomBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    hotel: Optional[Hotel] = None
    
    model_config = {
        "from_attributes": True
    }
