"""Stdout alert handler."""

import sys
from typing import Dict, List
from ..alerts.base import AlertBase
from ..rules.model import RuleResult


class StdoutAlert(AlertBase):
    """Sends alerts to stdout."""
    
    def send(self, anomalies: List[RuleResult], report: Dict) -> None:
        """
        Print alert to stdout.
        
        Args:
            anomalies: List of anomaly rule results
            report: Full report dictionary
        """
        if not anomalies:
            return
        
        print("\n" + "!" * 70, file=sys.stderr)
        print("LINMON ALERT: Anomalies Detected", file=sys.stderr)
        print("!" * 70, file=sys.stderr)
        
        overall = report.get("overall", {})
        triage = overall.get("triage_score", {})
        
        print(f"Severity: {triage.get('severity', 'unknown').upper()}", file=sys.stderr)
        print(f"Anomaly Count: {len(anomalies)}", file=sys.stderr)
        print("", file=sys.stderr)
        
        for anomaly in anomalies:
            print(
                f"  [{anomaly.rule_name}] {anomaly.metric} = {anomaly.value:.2f} "
                f"({anomaly.operator} {anomaly.threshold}) - Streak: {anomaly.streak}",
                file=sys.stderr
            )
        
        print("!" * 70 + "\n", file=sys.stderr)
