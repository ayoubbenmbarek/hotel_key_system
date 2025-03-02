# backend/app/models/reservation.py
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone

from app.models.base import BaseModel


class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Reservation(BaseModel):
    """
    Reservation model representing guest bookings
    """
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    room_id = Column(String, ForeignKey("room.id"), nullable=False)
    confirmation_code = Column(String, unique=True, index=True, nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)
    number_of_guests = Column(Integer, default=1)
    special_requests = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="reservations")
    room = relationship("Room", back_populates="reservations")
    digital_keys = relationship("DigitalKey", back_populates="reservation")
    
    def __repr__(self):
        return f"<Reservation {self.confirmation_code}>"
    
    def is_active(self):
        """Check if reservation is currently active"""
        now = datetime.now(timezone.utc)
        return (
            self.status in [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN] and
            self.check_in <= now <= self.check_out
        )
