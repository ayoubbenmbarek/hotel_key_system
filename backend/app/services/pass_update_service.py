# app/services/pass_update_service.py
import logging
from sqlalchemy.orm import Session

from app.models.digital_key import DigitalKey, KeyType
from app.models.reservation import Reservation
from app.models.room import Room
from app.models.user import User
from app.services.wallet_service import create_apple_wallet_pass, create_google_wallet_pass

logger = logging.getLogger(__name__)

def update_wallet_pass_status(db: Session, key_id: str, is_active: bool = True):
    """
    Update wallet pass status (active/inactive) and trigger a real-time update
    """
    try:
        # Get the key
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            logger.error(f"Key {key_id} not found")
            return
        
        # Get necessary data
        reservation = db.query(Reservation).filter(Reservation.id == key.reservation_id).first()
        if not reservation:
            logger.error(f"Reservation for key {key_id} not found")
            return
        
        room = db.query(Room).filter(Room.id == reservation.room_id).first()
        user = db.query(User).filter(User.id == reservation.user_id).first()
        
        # Prepare pass data
        pass_data = {
            "key_uuid": key.key_uuid,
            "room_number": room.room_number,
            "guest_name": f"{user.first_name} {user.last_name}",
            "check_in": reservation.check_in.isoformat(),
            "check_out": reservation.check_out.isoformat(),
            "nfc_lock_id": room.nfc_lock_id,
            "is_active": is_active,
            "voided": not is_active  # Make the pass appear voided if not active
        }
        
        # Regenerate the pass using existing functions
        if key.pass_type == KeyType.APPLE:
            create_apple_wallet_pass(pass_data)
            logger.info(f"Apple Wallet pass updated for key {key_id}")
        elif key.pass_type == KeyType.GOOGLE:
            create_google_wallet_pass(pass_data)
            logger.info(f"Google Wallet pass updated for key {key_id}")
        
        # In a production environment, you would send a push notification here
        # For now, we'll just log it
        logger.info(f"Would send push notification for key {key_id} status update")
        
    except Exception as e:
        logger.error(f"Error updating wallet pass status: {str(e)}")
