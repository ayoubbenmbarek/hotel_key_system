# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

from app.models.user import UserRole


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: Optional[UserRole] = UserRole.GUEST
    is_active: bool = True


# Properties to receive on user creation
class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @field_validator('phone_number')
    def validate_phone(cls, v):
        if v is not None:
            # Remove any non-digit characters
            v = ''.join(filter(str.isdigit, v))
            if len(v) < 10:
                raise ValueError('Phone number must have at least 10 digits')
        return v


# Properties to receive on user update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Properties shared by models returned from API
class UserInDBBase(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    # In Pydantic v2, orm_mode is replaced with model_config
    model_config = {
        "from_attributes": True
    }


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB but not returned
class UserInDB(UserInDBBase):
    hashed_password: str


# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
