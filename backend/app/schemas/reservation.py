# backend/app/schemas/reservation.py
from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Optional, List
from datetime import datetime

from app.schemas.room import Room
from app.schemas.user import User
from app.models.reservation import ReservationStatus


# Shared properties
class ReservationBase(BaseModel):
    user_id: str
    room_id: str
    check_in: datetime
    check_out: datetime
    number_of_guests: int = 1
    special_requests: Optional[str] = None
    
    @field_validator('check_out')
    def check_out_must_be_after_check_in(cls, v, info: ValidationInfo):
        """Validate that check-out date is after check-in date
        
        Args:
            v: The check-out date value being validated
            info: Validation information containing other field values
            
        Raises:
            ValueError: If check-out date is not after check-in date
            
        Returns:
            The validated check-out date
        """
        data = info.data  # Get the data dictionary
        if 'check_in' in data and v <= data['check_in']:
            raise ValueError('Check-out must be after check-in')
        return v


# Properties to receive on reservation creation
class ReservationCreate(ReservationBase):
    pass


# Properties to receive on reservation update
class ReservationUpdate(BaseModel):
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    number_of_guests: Optional[int] = None
    special_requests: Optional[str] = None
    status: Optional[ReservationStatus] = None


# Properties shared by models returned from API
class Reservation(ReservationBase):
    id: str
    confirmation_code: str
    status: ReservationStatus
    created_at: datetime
    updated_at: datetime
    room: Optional[Room] = None
    user: Optional[User] = None
    
    model_config = {
        "from_attributes": True
    }


# Properties for simple reservation list
class ReservationSummary(BaseModel):
    id: str
    confirmation_code: str
    room_number: str
    guest_name: str
    check_in: datetime
    check_out: datetime
    status: ReservationStatus
    
    model_config = {
        "from_attributes": True
    }
