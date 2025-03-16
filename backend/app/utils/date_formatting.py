import pytz
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def format_datetime_with_timezone(dt_str, timezone_name='Europe/Paris'):
    """
    Format a datetime string with proper timezone information
    
    Args:
        dt_str (str): ISO format datetime string
        timezone_name (str): Timezone name (e.g., 'Europe/Paris')
        
    Returns:
        str: Formatted datetime string with proper timezone
    """
    # Parse the datetime
    dt = datetime.fromisoformat(dt_str).replace(microsecond=0)
    
    # Ensure it has timezone info (assume UTC if none)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Convert to specified timezone
    local_dt = dt.astimezone(ZoneInfo(timezone_name))
    
    # Return ISO format with timezone info
    return local_dt.isoformat()
