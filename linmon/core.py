"""Core orchestration logic."""

from typing import Dict, List, Tuple
from pathlib import Path
from .config.loader import load_config
from .config.schema import Config
from .state.manager import StateManager
from .rules.engine import RuleEngine
from .monitors.cpu import CPUMonitor
from .monitors.storage import StorageMonitor
from .monitors.iostuck import IOStuckMonitor
from .monitors.base import MonitorBase
from .report.builder import ReportBuilder
from .report.text import TextReporter
from .report.json import JSONReporter
from .alerts.stdout import StdoutAlert
from .alerts.file import FileAlert
from .rules.model import RuleResult
from .util.fs import ensure_dir, atomic_write
from .util.time import now_iso


class LinmonCore:
    """Core orchestration for linmon."""
    
    def __init__(self, config_path: str):
        """
        Initialize linmon core.
        
        Args:
            config_path: Path to configuration file
        """
        self.config: Config = load_config(config_path)
        self.state_manager = StateManager(self.config.state_file)
        self.rule_engine = RuleEngine(self.state_manager)
        
        # Initialize monitors
        self.monitors: Dict[str, MonitorBase] = {}
        
        if "cpu" in self.config.monitors:
            cpu_config = self.config.monitors["cpu"]
            if cpu_config.enabled:
                self.monitors["cpu"] = CPUMonitor(cpu_config, self.rule_engine)
        
        if "storage" in self.config.monitors:
            storage_config = self.config.monitors["storage"]
            if storage_config.enabled:
                self.monitors["storage"] = StorageMonitor(storage_config, self.rule_engine)
        
        if "iostuck" in self.config.monitors:
            iostuck_config = self.config.monitors["iostuck"]
            if iostuck_config.enabled:
                self.monitors["iostuck"] = IOStuckMonitor(
                    iostuck_config, self.rule_engine, self.state_manager
                )
        
        # Initialize reporters
        self.text_reporter = TextReporter()
        self.json_reporter = JSONReporter()
        
        # Initialize alerts
        self.alerts: List = []
        if self.config.alerts.stdout:
            self.alerts.append(StdoutAlert())
        if self.config.alerts.file:
            self.alerts.append(FileAlert(self.config.alerts.file))
    
    def run(self) -> Tuple[int, str, str]:
        """
        Run monitoring check.
        
        Returns:
            Tuple of (exit_code, text_report, json_report)
            Exit codes: 0=OK, 1=warnings, 2=critical
        """
        # Update last run timestamp
        self.state_manager.update_last_run(now_iso())
        
        # Evaluate all monitors
        all_results: Dict[str, List[RuleResult]] = {}
        all_anomalies: List[RuleResult] = []
        
        for monitor_name, monitor in self.monitors.items():
            results = monitor.evaluate()
            all_results[monitor_name] = results
            all_anomalies.extend([r for r in results if r.anomaly])
        
        # Build report
        report_builder = ReportBuilder()
        report = report_builder.build(self.monitors, all_results)
        
        # Generate reports
        text_report = self.text_reporter.format(report)
        json_report = self.json_reporter.format(report)
        
        # Save reports
        ensure_dir(self.config.report_dir)
        timestamp = now_iso().replace(":", "-").replace(".", "-")
        text_path = Path(self.config.report_dir) / f"report-{timestamp}.txt"
        json_path = Path(self.config.report_dir) / f"report-{timestamp}.json"
        
        atomic_write(str(text_path), text_report)
        atomic_write(str(json_path), json_report)
        
        # Send alerts if anomalies exist
        if all_anomalies:
            for alert in self.alerts:
                alert.send(all_anomalies, report)
        
        # Save state
        self.state_manager.save()
        
        # Determine exit code
        overall = report.get("overall", {})
        triage = overall.get("triage_score", {})
        severity = triage.get("severity", "low")
        
        if severity == "critical":
            exit_code = 2
        elif severity in ("high", "medium") or all_anomalies:
            exit_code = 1
        else:
            exit_code = 0
        
        return (exit_code, text_report, json_report)
