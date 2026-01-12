"""Collector for PSI (Pressure Stall Information) metrics."""

from pathlib import Path
from typing import Dict, Optional


class PSICollector:
    """Collects PSI metrics from /proc/pressure/."""
    
    def __init__(self):
        """Initialize collector."""
        self.io_path = Path("/proc/pressure/io")
    
    def is_available(self) -> bool:
        """Check if PSI is available on this system."""
        return self.io_path.exists()
    
    def read_io_pressure(self) -> Optional[Dict[str, float]]:
        """
        Read IO pressure from /proc/pressure/io.
        
        Returns:
            Dictionary with avg10, avg60, avg300, total, or None if unavailable
        """
        if not self.is_available():
            return None
        
        try:
            with open(self.io_path, "r") as f:
                line = f.readline()
            
            # Format: some avg10=0.00 avg60=0.00 avg300=0.00 total=0
            parts = line.strip().split()
            result = {}
            
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    try:
                        result[key] = float(value)
                    except ValueError:
                        pass
            
            return result if result else None
        except Exception:
            return None
