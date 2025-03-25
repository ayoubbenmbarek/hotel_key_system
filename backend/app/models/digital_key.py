# backend/app/models/digital_key.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum
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
    __tablename__ = "digitalkey"
    
    # Your existing columns
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
    auth_token = Column(String)
    # auth_token = Column(String, nullable=True) TODO: check if migration needed if we change this
    
    # Relationships
    reservation = relationship("Reservation", back_populates="digital_keys")
    events = relationship("KeyEvent", back_populates="digital_key")
    device_registrations = relationship("DeviceRegistration", back_populates="digital_key", cascade="all, delete-orphan")
    
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
