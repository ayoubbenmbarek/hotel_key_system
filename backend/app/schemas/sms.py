from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class SMSResponseModel(BaseModel):
    message: str
    invalid_numbers: Optional[List[str]] = None
    failed_numbers: Optional[List[str]] = None
    # timestamp: datetime = None
