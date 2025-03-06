from app.models.device import DeviceRegistration


def get_registered_devices(pass_type_id, serial_number, db):
    """Get all registered device tokens for a digital key"""
    registrations = db.query(DeviceRegistration).filter(
        DeviceRegistration.pass_type_id == pass_type_id,
        DeviceRegistration.serial_number == serial_number,
        DeviceRegistration.active == True
    ).all()
    
    return [reg.push_token for reg in registrations]
