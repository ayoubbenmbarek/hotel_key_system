# backend/app/models/user.py
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HOTEL_STAFF = "hotel_staff"
    GUEST = "guest"


class User(BaseModel):
    """
    User model for all types of users in the system
    """
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone_number = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.GUEST, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    reservations = relationship("Reservation", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
