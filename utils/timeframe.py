"""
Timeframe Utilities
Parse and convert various timeframe formats
"""
from datetime import datetime, timedelta
from typing import Tuple
import re

def parse_timeframe(timeframe: str) -> Tuple[datetime, datetime]:
    """
    Parse timeframe string and return start/end timestamps
    
    Supports formats: "2h", "30m", "7d", "1w"
    
    Args:
        timeframe: Time period string (e.g., "2h", "30m", "7d")
        
    Returns:
        Tuple of (from_time, to_time) as datetime objects
        
    Raises:
        ValueError: If timeframe format is invalid
    """
    match = re.match(r'^(\d+)([mhdw])$', timeframe.lower())
    
    if not match:
        raise ValueError(
            f"Invalid timeframe format: '{timeframe}'. "
            "Expected format: <number><unit> (e.g., '2h', '30m', '7d', '1w')"
        )
    
    value = int(match.group(1))
    unit = match.group(2)
    
    # Map units to timedelta kwargs
    unit_mapping = {
        'm': 'minutes',
        'h': 'hours',
        'd': 'days',
        'w': 'weeks'
    }
    
    now = datetime.utcnow()
    delta = timedelta(**{unit_mapping[unit]: value})
    from_time = now - delta
    
    return from_time, now

def timeframe_to_dynatrace(timeframe: str) -> str:
    """
    Convert timeframe to Dynatrace API format
    
    Args:
        timeframe: Time period string (e.g., "2h")
        
    Returns:
        Formatted time range for Dynatrace API (e.g., "from=...&to=...")
    """
    from_time, to_time = parse_timeframe(timeframe)
    from_str = from_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_str = to_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return from_str, to_str

def human_readable_timeframe(timeframe: str) -> str:
    """
    Convert timeframe to human-readable format
    
    Args:
        timeframe: Time period string (e.g., "2h")
        
    Returns:
        Human-readable string (e.g., "Last 2 hours")
    """
    match = re.match(r'^(\d+)([mhdw])$', timeframe.lower())
    
    if not match:
        return timeframe
    
    value = int(match.group(1))
    unit = match.group(2)
    
    unit_names = {
        'm': 'minute' if value == 1 else 'minutes',
        'h': 'hour' if value == 1 else 'hours',
        'd': 'day' if value == 1 else 'days',
        'w': 'week' if value == 1 else 'weeks'
    }
    
    return f"Last {value} {unit_names[unit]}"
