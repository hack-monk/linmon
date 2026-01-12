"""File-based alert handler."""

from typing import Dict, List
from pathlib import Path
from ..alerts.base import AlertBase
from ..rules.model import RuleResult
from ..util.fs import ensure_dir
from ..util.time import now_iso


class FileAlert(AlertBase):
    """Sends alerts to a file (append mode)."""
    
    def __init__(self, filepath: str):
        """
        Initialize file alert.
        
        Args:
            filepath: Path to alert log file
        """
        self.filepath = filepath
    
    def send(self, anomalies: List[RuleResult], report: Dict) -> None:
        """
        Append alert to file.
        
        Args:
            anomalies: List of anomaly rule results
            report: Full report dictionary
        """
        if not anomalies:
            return
        
        ensure_dir(str(Path(self.filepath).parent))
        
        lines = []
        lines.append(f"[{now_iso()}] LINMON ALERT")
        lines.append(f"Anomaly Count: {len(anomalies)}")
        
        overall = report.get("overall", {})
        triage = overall.get("triage_score", {})
        lines.append(f"Severity: {triage.get('severity', 'unknown').upper()}")
        lines.append("")
        
        for anomaly in anomalies:
            lines.append(
                f"  [{anomaly.rule_name}] {anomaly.metric} = {anomaly.value:.2f} "
                f"({anomaly.operator} {anomaly.threshold}) - Streak: {anomaly.streak}"
            )
        
        lines.append("")
        lines.append("-" * 70)
        lines.append("")
        
        try:
            with open(self.filepath, "a") as f:
                f.write("\n".join(lines))
        except Exception:
            # Fail silently on file write errors
            pass
