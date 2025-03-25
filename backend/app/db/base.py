# Import all the models here so Alembic can detect them
from app.db.session import Base

# First, import models that don't depend on other models
from app.models.user import User
from app.models.room import Room

# Then import models that depend on the above models
from app.models.reservation import Reservation  # Depends on User and Room

# Finally import models that depend on Reservation
from app.models.digital_key import DigitalKey   # Depends on Reservation
from app.models.key_event import KeyEvent       # Depends on DigitalKey
from app.models.device import DeviceRegistration  # Depends on DigitalKey 