# backend/app/schemas/digital_key.py
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

from app.models.digital_key import KeyStatus, KeyType


# Shared properties
class DigitalKeyBase(BaseModel):
    reservation_id: str
    pass_type: KeyType


# Properties to receive on key creation
class DigitalKeyCreate(DigitalKeyBase):
    send_email: bool = True


# Properties to receive on key update
class DigitalKeyUpdate(BaseModel):
    is_active: Optional[bool] = None
    status: Optional[KeyStatus] = None
    valid_until: Optional[datetime] = None


# Properties for extending key validity
class KeyExtension(BaseModel):
    new_end_date: datetime
    
    @validator('new_end_date')
    def validate_end_date(cls, v):
        if v < datetime.utcnow():
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
    
    class Config:
        orm_mode = True


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


# Key event schemas
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
    
    class Config:
        orm_mode = True
