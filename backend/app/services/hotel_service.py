from typing import Optional
from sqlalchemy.orm import Session
from app.models.hotel import Hotel  # Adjust import based on your actual model structure
import logging

# Cache the hotel name to avoid frequent DB queries
_hotel_name_cache = {}

logger = logging.getLogger(__name__)

def get_hotel_name(db: Session, hotel_id: Optional[str] = None) -> str:
    """
    Get the hotel name from the database.
    If hotel_id is None, returns the default hotel name.
    Uses caching to improve performance.
    """
    # If no hotel_id is provided, return error message instead of default
    if not hotel_id:
        return "Hotel"
    
    # Check cache first
    if hotel_id in _hotel_name_cache:
        return _hotel_name_cache[hotel_id]
    
    # Query the database for the specific hotel
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    
    if not hotel:
        # Log warning if hotel not found with specific ID
        logger.warning(f"Hotel with ID {hotel_id} not found in database")
        result = "Unknown Hotel"
    else:
        result = hotel.name
    
    # Cache the result
    _hotel_name_cache[hotel_id] = result
    return result
