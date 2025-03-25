from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import Column, String, DateTime, Text
from app.db.session import Base

class DeviceLog(Base):
    __tablename__ = "device_logs"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String, nullable=False)
    pass_type = Column(String, nullable=False)
    serial_number = Column(String, nullable=False)
    log_level = Column(String, default="info")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
