"""Text format report generator."""

from typing import Dict, List


class TextReporter:
    """Generates human-readable text reports."""
    
    def format(self, report: Dict) -> str:
        """
        Format report as text.
        
        Args:
            report: Report dictionary from ReportBuilder
            
        Returns:
            Formatted text string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("linmon Report")
        lines.append("=" * 70)
        lines.append(f"Timestamp: {report['timestamp']}")
        lines.append("")
        
        # Overall summary
        overall = report["overall"]
        triage = overall["triage_score"]
        lines.append(f"Overall Status: {triage['severity'].upper()}")
        lines.append(f"Triage Score: {triage['score']}/100")
        lines.append(f"Anomalies: {overall['anomaly_count']}")
        
        if triage.get("factors"):
            lines.append("Factors:")
            for factor in triage["factors"]:
                lines.append(f"  - {factor}")
        
        lines.append("")
        lines.append("-" * 70)
        
        # Monitor details
        for monitor_name, monitor_data in report["monitors"].items():
            lines.append(f"\nMonitor: {monitor_name.upper()}")
            lines.append("-" * 70)
            
            # Metrics
            metrics = monitor_data.get("metrics", {})
            if metrics:
                lines.append("Metrics:")
                for key, value in sorted(metrics.items()):
                    if isinstance(value, float):
                        lines.append(f"  {key}: {value:.2f}")
                    else:
                        lines.append(f"  {key}: {value}")
                lines.append("")
            
            # Results
            results = monitor_data.get("results", [])
            anomalies = monitor_data.get("anomalies", [])
            
            if anomalies:
                lines.append("ANOMALIES:")
                for anomaly in anomalies:
                    lines.append(f"  [{anomaly['rule_name']}] {anomaly['metric']} = {anomaly['value']:.2f}")
                    lines.append(f"    Threshold: {anomaly['operator']} {anomaly['threshold']}")
                    lines.append(f"    Streak: {anomaly['streak']}/{anomaly['consecutive_required']}")
                    lines.append("")
            elif results:
                lines.append("Status: OK (no anomalies)")
                lines.append("")
            
            # Suggested commands
            commands = monitor_data.get("suggested_commands", [])
            if commands and anomalies:
                lines.append("Suggested Commands:")
                for cmd in commands[:5]:  # Limit to 5
                    lines.append(f"  $ {cmd}")
                lines.append("")
        
        # Global suggested commands
        global_commands = report.get("suggested_commands", [])
        if global_commands and overall["anomaly_count"] > 0:
            lines.append("-" * 70)
            lines.append("General Diagnostic Commands:")
            for cmd in global_commands[:10]:
                lines.append(f"  $ {cmd}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)
