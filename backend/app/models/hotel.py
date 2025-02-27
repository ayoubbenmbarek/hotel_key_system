# backend/app/models/hotel.py
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Hotel(BaseModel):
    """
    Hotel model to represent properties using the system
    """
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    country = Column(String, nullable=False)
    postal_code = Column(String)
    phone_number = Column(String, nullable=False)
    email = Column(String)
    website = Column(String)
    logo_url = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    rooms = relationship("Room", back_populates="hotel")
    
    def __repr__(self):
        return f"<Hotel {self.name}>"


class HotelStaff(BaseModel):
    """
    Association between users and hotels for staff members
    """
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    hotel_id = Column(String, ForeignKey("hotel.id"), nullable=False)
    position = Column(String)
    
    # Relationships
    user = relationship("User")
    hotel = relationship("Hotel")
    
    def __repr__(self):
        return f"<HotelStaff {self.user_id} at {self.hotel_id}>"
