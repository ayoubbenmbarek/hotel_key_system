from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class DeviceRegistration(BaseModel):
    __tablename__ = "device_registrations"
    
    device_library_id = Column(String, nullable=False)
    pass_type_id = Column(String, nullable=False)
    serial_number = Column(String, nullable=False)
    push_token = Column(String, nullable=False)
    active = Column(Boolean, server_default='true')
    digital_key_id = Column(String, ForeignKey("digitalkey.id"))
    
    # Relationship
    digital_key = relationship("DigitalKey", back_populates="device_registrations")
    
    # Composite unique constraint
    __table_args__ = (
        UniqueConstraint('device_library_id', 'pass_type_id', 'serial_number', name='device_pass_unique'),
    )
