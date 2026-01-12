"""IO-stuck and hung task monitor."""

from typing import Dict, List
from ..monitors.base import MonitorBase
from ..collectors.psi import PSICollector
from ..collectors.logs import LogCollector
from ..collectors.processes import ProcessCollector
from ..state.manager import StateManager
from ..config.schema import IOStuckConfig


class IOStuckMonitor(MonitorBase):
    """Monitors for IO-stuck conditions via logs, PSI, and D-state tasks."""
    
    def __init__(self, config: IOStuckConfig, rule_engine, state_manager: StateManager):
        """Initialize IO-stuck monitor."""
        super().__init__("iostuck", config, rule_engine)
        self.config: IOStuckConfig = config
        self.psi_collector = PSICollector()
        self.log_collector = LogCollector()
        self.process_collector = ProcessCollector()
        self.state_manager = state_manager
    
    def collect_metrics(self) -> Dict[str, float]:
        """Collect IO-stuck metrics."""
        metrics = {}
        
        # Hung tasks from kernel logs
        cursor = self.state_manager.get_log_cursor("kernel")
        log_lines, new_cursor = self.log_collector.collect_kernel_logs(cursor)
        hung_task_count = self.log_collector.find_hung_tasks(log_lines)
        metrics["hung_task_count"] = float(hung_task_count)
        
        # Update cursor
        if new_cursor:
            self.state_manager.set_log_cursor("kernel", new_cursor)
        
        # PSI IO pressure (if available)
        if self.psi_collector.is_available():
            psi_data = self.psi_collector.read_io_pressure()
            if psi_data:
                metrics["psi_io_avg10"] = psi_data.get("avg10", 0.0)
                metrics["psi_io_avg60"] = psi_data.get("avg60", 0.0)
                metrics["psi_io_avg300"] = psi_data.get("avg300", 0.0)
        
        # D-state tasks
        d_state_tasks = self.process_collector.get_d_state_tasks()
        metrics["d_state_task_count"] = float(len(d_state_tasks))
        
        return metrics
    
    def get_suggested_commands(self) -> List[str]:
        """Get suggested diagnostic commands."""
        return [
            "ps aux | grep ' D '",
            "dmesg | tail -50",
            "journalctl -k --since '10 minutes ago' | grep -i 'hung\\|blocked\\|stuck'",
            "iostat -x 1 5",
            "cat /proc/pressure/io",
        ]
