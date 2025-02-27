# backend/app/models/base.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declared_attr

from app.db.session import Base


class BaseModel(Base):
    """
    Base model class with common fields and functionality
    """
    __abstract__ = True
    
    # Use table name based on class name
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    # Common columns
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
