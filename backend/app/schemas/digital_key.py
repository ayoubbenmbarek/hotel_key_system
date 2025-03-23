# backend/app/schemas/digital_key.py
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, timezone

from app.models.digital_key import KeyStatus, KeyType


# Shared properties
class DigitalKeyBase(BaseModel):
    reservation_id: str
    pass_type: KeyType


# Properties to receive on key creation
class DigitalKeyCreate(DigitalKeyBase):
    send_email: bool = True
    # TODO: add for sms send
    alternative_email: Optional[str] = None
    send_sms: bool = False
    phone_numbers: Optional[List[str]] = None


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


# Properties shared by models returned from API
class DigitalKeyInDBBase(DigitalKeyBase):
    id: str
    key_uuid: str
    pass_url: Optional[str]
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    status: KeyStatus
    activated_at: Optional[datetime]
    last_used: Optional[datetime]
    access_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


# Additional properties to return via API
class DigitalKey(DigitalKeyInDBBase):
    pass


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


class KeyEvent(KeyEventBase):
    id: str
    timestamp: datetime
    
    model_config = {
        "from_attributes": True
    }
