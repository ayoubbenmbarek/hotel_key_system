# backend/app/models/digital_key.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timezone

from app.models.base import BaseModel


class KeyStatus(str, enum.Enum):
    CREATED = "created"
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class KeyType(str, enum.Enum):
    APPLE = "apple"
    GOOGLE = "google"


class DigitalKey(BaseModel):
    """
    Digital Key model for virtual room keys
    """
    reservation_id = Column(String, ForeignKey("reservation.id"), nullable=False)
    key_uuid = Column(String, unique=True, index=True, nullable=False)
    pass_url = Column(String)
    pass_type = Column(Enum(KeyType), nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    status = Column(Enum(KeyStatus), default=KeyStatus.CREATED, nullable=False)
    activated_at = Column(DateTime)
    last_used = Column(DateTime)
    access_count = Column(Integer, default=0)
    
    # Relationships
    reservation = relationship("Reservation", back_populates="digital_keys")
    events = relationship("KeyEvent", back_populates="digital_key")
    
    def __repr__(self):
        return f"<DigitalKey {self.key_uuid}>"
    
    def is_valid(self):
        """Check if key is currently valid"""
        now = datetime.now(timezone.utc)
        return (
            self.is_active and
            self.status in [KeyStatus.CREATED, KeyStatus.ACTIVE] and
            self.valid_from <= now <= self.valid_until
        )


class KeyEvent(BaseModel):
    """
    Event log for digital key usage
    """
    key_id = Column(String, ForeignKey("digitalkey.id"))
    event_type = Column(String, nullable=False)  # access_attempt, access_granted, access_denied
    device_info = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    location = Column(String)
    status = Column(String)  # success, failure
    details = Column(String)  # Additional details about the event
    
    # Relationships
    digital_key = relationship("DigitalKey", back_populates="events")
    
    def __repr__(self):
        return f"<KeyEvent {self.event_type} at {self.timestamp}>"
