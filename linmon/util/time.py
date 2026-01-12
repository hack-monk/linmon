"""Time utilities."""

from datetime import datetime, timedelta
from typing import Optional


def now_iso() -> str:
    """Return current time as ISO 8601 string."""
    return datetime.utcnow().isoformat() + "Z"


def parse_duration(s: str) -> float:
    """
    Parse duration string to seconds.
    
    Supports formats like: "5m", "30s", "1h", "2.5m"
    
    Args:
        s: Duration string
        
    Returns:
        Duration in seconds as float
    """
    s = s.strip().lower()
    if s.endswith("s"):
        return float(s[:-1])
    elif s.endswith("m"):
        return float(s[:-1]) * 60
    elif s.endswith("h"):
        return float(s[:-1]) * 3600
    elif s.endswith("d"):
        return float(s[:-1]) * 86400
    else:
        # Assume seconds if no unit
        return float(s)
