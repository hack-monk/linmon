"""Collector for /proc filesystem data."""

import time
from typing import Dict, Optional, Tuple
from pathlib import Path


class ProcFSCollector:
    """Collects CPU and system metrics from /proc."""
    
    def __init__(self):
        """Initialize collector."""
        self._last_cpu_times: Optional[Tuple[float, Dict[str, float]]] = None
    
    def read_stat(self) -> Dict[str, float]:
        """
        Read /proc/stat and return CPU times.
        
        Returns:
            Dictionary with cpu times (user, nice, system, idle, iowait, etc.)
        """
        stat_path = Path("/proc/stat")
        if not stat_path.exists():
            return {}
        
        try:
            with open(stat_path, "r") as f:
                line = f.readline()
            
            # Parse: cpu  user nice system idle iowait irq softirq ...
            parts = line.strip().split()
            if parts[0] != "cpu" or len(parts) < 5:
                return {}
            
            return {
                "user": float(parts[1]),
                "nice": float(parts[2]),
                "system": float(parts[3]),
                "idle": float(parts[4]),
                "iowait": float(parts[5]) if len(parts) > 5 else 0.0,
                "irq": float(parts[6]) if len(parts) > 6 else 0.0,
                "softirq": float(parts[7]) if len(parts) > 7 else 0.0,
            }
        except Exception:
            return {}
    
    def read_loadavg(self) -> Dict[str, float]:
        """
        Read /proc/loadavg.
        
        Returns:
            Dictionary with load1, load5, load15
        """
        loadavg_path = Path("/proc/loadavg")
        if not loadavg_path.exists():
            return {}
        
        try:
            with open(loadavg_path, "r") as f:
                line = f.readline()
            
            parts = line.strip().split()
            if len(parts) < 3:
                return {}
            
            return {
                "load1": float(parts[0]),
                "load5": float(parts[1]),
                "load15": float(parts[2]),
            }
        except Exception:
            return {}
    
    def get_cpu_percent(self, sample_seconds: float = 2.0) -> Optional[float]:
        """
        Calculate CPU usage percentage by sampling /proc/stat.
        
        Args:
            sample_seconds: Duration to sample
            
        Returns:
            CPU usage percentage (0-100) or None on error
        """
        # First reading
        cpu_times1 = self.read_stat()
        if not cpu_times1:
            return None
        
        time.sleep(sample_seconds)
        
        # Second reading
        cpu_times2 = self.read_stat()
        if not cpu_times2:
            return None
        
        # Calculate deltas
        total1 = sum(cpu_times1.values())
        total2 = sum(cpu_times2.values())
        
        if total2 <= total1:
            return None  # No change or invalid
        
        # Idle delta
        idle_delta = cpu_times2["idle"] - cpu_times1["idle"]
        total_delta = total2 - total1
        
        # CPU usage = (1 - idle/total) * 100
        cpu_percent = (1.0 - (idle_delta / total_delta)) * 100.0
        
        return max(0.0, min(100.0, cpu_percent))
