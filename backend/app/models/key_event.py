from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional

from app.models.base import BaseModel

class EventType(str, Enum):
    KEY_CREATED = "key_created"
    KEY_ACTIVATED = "key_activated"
    KEY_DEACTIVATED = "key_deactivated"
    PHYSICAL_ACCESS_ATTEMPT = "physical_access_attempt"
    PHYSICAL_ACCESS_GRANTED = "physical_access_granted"
    PHYSICAL_ACCESS_DENIED = "physical_access_denied"
    DIGITAL_ACCESS = "digital_access"
    KEY_EMAIL_SENT = "key_email_sent"
    KEY_EMAIL_FAILED = "key_email_failed"
    KEY_SMS_SENT = "key_sms_sent"
    KEY_SMS_FAILED = "key_sms_failed"
    KEY_UPDATED = "key_updated"
    KEY_EXTENDED = "key_extended"

class KeyEvent(BaseModel):
    __tablename__ = "keyevent"

    key_id = Column(String, ForeignKey("digitalkey.id"))
    event_type = Column(String, nullable=False)
    device_info = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    location = Column(String, nullable=True)
    status = Column(String, nullable=True)
    details = Column(String, nullable=True)

    # Relationship
    digital_key = relationship("DigitalKey", back_populates="events")

    @classmethod
    def create(cls, key_id: str, event_type: str, **kwargs) -> "KeyEvent":
        # Validate event type
        if event_type not in EventType.__members__.values():
            raise ValueError(f"Invalid event type: {event_type}")
        
        # Validate status
        status = kwargs.get('status', 'success')
        valid_statuses = ['success', 'error', 'pending']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        # Create the event with all fields
        return cls(
            key_id=key_id,
            event_type=event_type,
            device_info=kwargs.get('device_info'),
            status=status,
            details=kwargs.get('details'),
            location=kwargs.get('location'),
            timestamp=datetime.now(timezone.utc)
        )
