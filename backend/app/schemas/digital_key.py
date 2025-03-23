# backend/app/schemas/digital_key.py
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum

from app.models.digital_key import KeyStatus, KeyType
from app.schemas.reservation import Reservation


# Shared properties
class DigitalKeyBase(BaseModel):
    reservation_id: str
    pass_type: KeyType
    key_uuid: str
    pass_url: Optional[str] = None
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True
    status: KeyStatus = KeyStatus.CREATED
    activated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    access_count: int = 0


# Properties to receive on key creation
class DigitalKeyCreate(BaseModel):
    reservation_id: str
    pass_type: KeyType = KeyType.APPLE
    send_email: bool = False
    send_sms: bool = False
    phone_numbers: Optional[list[str]] = None


# Properties to receive on key update
class DigitalKeyUpdate(BaseModel):
    is_active: Optional[bool] = None
    status: Optional[KeyStatus] = None
    valid_until: Optional[datetime] = None


# Properties for extending key validity
class KeyExtension(BaseModel):
    new_end_date: datetime
    
    @field_validator('new_end_date')
    def validate_end_date(cls, v):
        # Convert to timezone-aware datetime if it's naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
            
        # Now compare with current time (also timezone-aware)
        now = datetime.now(timezone.utc)
        if v < now:
            raise ValueError('New end date must be in the future')
        return v


# Properties for key events
class KeyEvent(BaseModel):
    key_id: str
    event_type: str
    device_info: Optional[str] = None
    status: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }


# Properties shared by models returned from API
class DigitalKey(DigitalKeyBase):
    id: str
    created_at: datetime
    updated_at: datetime
    reservation: Optional[Reservation] = None

    model_config = {
        "from_attributes": True
    }


# Key verification schemas
class KeyVerificationRequest(BaseModel):
    key_uuid: str
    lock_id: str
    device_info: Optional[str] = None
    location: Optional[str] = None


class KeyVerification(BaseModel):
    is_valid: bool
    message: str
    room_number: Optional[str] = None
    guest_name: Optional[str] = None


# Key event schemas TODO: move to key_event.py
class KeyEventBase(BaseModel):
    key_id: str
    event_type: str
    device_info: Optional[str] = None
    location: Optional[str] = None
    status: str
    details: Optional[str] = None


class KeyEventCreate(KeyEventBase):
    pass
