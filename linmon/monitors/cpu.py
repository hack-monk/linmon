"""CPU usage monitor."""

from typing import Dict, List
from ..monitors.base import MonitorBase
from ..collectors.procfs import ProcFSCollector
from ..config.schema import CPUConfig


class CPUMonitor(MonitorBase):
    """Monitors CPU usage and load average."""
    
    def __init__(self, config: CPUConfig, rule_engine):
        """Initialize CPU monitor."""
        super().__init__("cpu", config, rule_engine)
        self.config: CPUConfig = config
        self.collector = ProcFSCollector()
    
    def collect_metrics(self) -> Dict[str, float]:
        """Collect CPU metrics."""
        metrics = {}
        
        # CPU percentage
        cpu_percent = self.collector.get_cpu_percent(self.config.sample_seconds)
        if cpu_percent is not None:
            metrics["cpu_percent"] = cpu_percent
        
        # Load average
        loadavg = self.collector.read_loadavg()
        if loadavg:
            metrics.update({
                "load1": loadavg.get("load1", 0.0),
                "load5": loadavg.get("load5", 0.0),
                "load15": loadavg.get("load15", 0.0),
            })
        
        return metrics
    
    def get_suggested_commands(self) -> List[str]:
        """Get suggested diagnostic commands."""
        return [
            "top -bn1 | head -20",
            "ps aux --sort=-%cpu | head -10",
            "vmstat 1 5",
            "iostat -x 1 5",
        ]
