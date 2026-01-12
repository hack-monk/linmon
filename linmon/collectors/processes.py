"""Collector for process state information."""

from typing import List, Dict
from ..util.shell import safe_subprocess, which


class ProcessCollector:
    """Collects process state information."""
    
    def __init__(self):
        """Initialize collector."""
        self.ps_path = which("ps")
    
    def get_d_state_tasks(self) -> List[Dict[str, str]]:
        """
        Get list of processes in D (uninterruptible sleep) state.
        
        Returns:
            List of dicts with pid, state, comm, wchan
        """
        if not self.ps_path:
            return []
        
        # ps -eo pid,state,comm,wchan:32
        cmd = [self.ps_path, "-eo", "pid,state,comm,wchan:32"]
        returncode, stdout, stderr = safe_subprocess(cmd, timeout=5.0)
        
        if returncode != 0 or not stdout:
            return []
        
        tasks = []
        lines = stdout.strip().split("\n")
        
        # Skip header line
        for line in lines[1:]:
            parts = line.split(None, 3)
            if len(parts) >= 4:
                pid, state, comm, wchan = parts[0], parts[1], parts[2], parts[3]
                if state == "D":
                    tasks.append({
                        "pid": pid,
                        "state": state,
                        "comm": comm,
                        "wchan": wchan,
                    })
        
        return tasks
