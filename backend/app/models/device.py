from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from datetime import datetime, timezone
import uuid

from app.models.base import BaseModel


class DeviceRegistration(BaseModel):
    __tablename__ = "device_registrations"
    
    # Make sure id is defined
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    device_library_id = Column(String, nullable=False)
    pass_type_id = Column(String, nullable=False) 
    serial_number = Column(String, nullable=False)
    push_token = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    active = Column(Boolean, default=True)
    
    # Foreign key to DigitalKey - using correct table name
    digital_key_id = Column(String, ForeignKey("digitalkey.id"))
    digital_key = relationship("DigitalKey", back_populates="device_registrations")
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('device_library_id', 'pass_type_id', 'serial_number', name='device_pass_unique'),
    )
