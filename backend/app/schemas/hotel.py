# backend/app/schemas/hotel.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Shared properties
class HotelBase(BaseModel):
    name: str
    address: str
    city: str
    state: str
    country: str
    postal_code: Optional[str] = None
    phone_number: str
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None


# Properties to receive on hotel creation
class HotelCreate(HotelBase):
    pass


# Properties to receive on hotel update
class HotelUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None


# Properties shared by models returned from API
class Hotel(HotelBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
