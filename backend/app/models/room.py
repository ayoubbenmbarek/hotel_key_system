# backend/app/models/room.py
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class RoomType(str, enum.Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    EXECUTIVE = "executive"
    PRESIDENTIAL = "presidential"


class Room(BaseModel):
    """
    Room model representing individual hotel rooms
    """
    hotel_id = Column(String, ForeignKey("hotel.id"), nullable=False)
    room_number = Column(String, nullable=False)
    floor = Column(Integer)
    room_type = Column(Enum(RoomType), default=RoomType.STANDARD, nullable=False)
    max_occupancy = Column(Integer, default=2)
    nfc_lock_id = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    hotel = relationship("Hotel", back_populates="rooms")
    reservations = relationship("Reservation", back_populates="room")
    
    def __repr__(self):
        return f"<Room {self.room_number} at {self.hotel_id}>"


class RoomLock(BaseModel):
    """
    Additional information about room locks
    """
    room_id = Column(String, ForeignKey("room.id"), nullable=False)
    lock_serial = Column(String, unique=True, nullable=False)
    lock_model = Column(String)
    firmware_version = Column(String)
    battery_level = Column(Integer)  # Percentage
    last_connection = Column(String)
    
    # Relationships
    room = relationship("Room")
    
    def __repr__(self):
        return f"<RoomLock for {self.room_id}>"
