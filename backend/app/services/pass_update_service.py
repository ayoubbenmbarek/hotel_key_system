# app/services/pass_update_service.py
import logging
from sqlalchemy.orm import Session

from app.models.digital_key import DigitalKey, KeyType
from app.models.reservation import Reservation
from app.services.wallet_push_service import send_push_notifications_production
from app.services.wallet_service import settings

from app.models.room import Room
from app.models.user import User
from app.services.wallet_service import create_apple_wallet_pass, create_google_wallet_pass
from app.models.key_event import KeyEvent
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def update_wallet_pass_status(db: Session, key_id: str, is_active: bool = True):
    """
    Update wallet pass status (active/inactive) and trigger a real-time update
    """
    logger.info(f"Updating wallet pass status for key {key_id} to is_active={is_active}")
    try:
        # Get the key
        key = db.query(DigitalKey).filter(DigitalKey.id == key_id).first()
        if not key:
            logger.error(f"Key {key_id} not found")
            return
        
        # Update key status in database to ensure it's consistent
        key.is_active = is_active
        key.status = "ACTIVE" if is_active else "REVOKED"
        key.updated_at = datetime.now(timezone.utc)
        
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
        
        # Create a key event to track this update
        event = KeyEvent(
            key_id=key.id,
            event_type="wallet_pass_updated",
            device_info="System",
            status="pending",
            details=f"Updating wallet pass status to {'active' if is_active else 'inactive'}",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(event)
        db.commit()
        
        try:
            # Regenerate the pass using existing functions
            if key.pass_type == KeyType.APPLE:
                create_apple_wallet_pass(pass_data, db)
                logger.info(f"Apple Wallet pass updated for key {key_id}")
                
                # Send push notification to update the wallet pass
                push_result = send_push_notifications_production(settings.APPLE_PASS_TYPE_ID, key.key_uuid, db)
                logger.info(f"Push notification result for key {key_id}: {push_result}")
                
                # Update the event status
                event.status = "success"
                event.details += f" | Push notification sent to {push_result} devices"
                db.commit()
                
            elif key.pass_type == KeyType.GOOGLE:
                create_google_wallet_pass(pass_data)
                logger.info(f"Google Wallet pass updated for key {key_id}")
                
                # Update the event status
                event.status = "success"
                event.details += " | Google Wallet pass updated"
                db.commit()
        
        except Exception as update_error:
            logger.error(f"Error during pass update: {str(update_error)}")
            # Mark the event as failed
            event.status = "error"
            event.details += f" | Error: {str(update_error)}"
            db.commit()
            # Re-raise to be caught by outer try/except
            raise
        
    except Exception as e:
        logger.error(f"Error updating wallet pass status: {str(e)}")
        # Create a failure event if one wasn't already created
        try:
            event = KeyEvent(
                key_id=key_id,
                event_type="wallet_pass_update_failed",
                device_info="System",
                status="error",
                details=f"Failed to update wallet pass: {str(e)}",
                timestamp=datetime.now(timezone.utc)
            )
            db.add(event)
            db.commit()
        except Exception:
            # Don't let an error in creating the error event prevent us from handling the original error
            logger.error("Failed to create error event")
