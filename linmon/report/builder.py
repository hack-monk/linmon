"""Report builder that aggregates monitor results."""

from typing import Dict, List
from ..rules.model import RuleResult
from ..triage.model import TriageScore
from ..triage.scorer import TriageScorer
from ..monitors.base import MonitorBase


class ReportBuilder:
    """Builds reports from monitor results."""
    
    def __init__(self):
        """Initialize report builder."""
        self.scorer = TriageScorer()
    
    def build(
        self,
        monitors: Dict[str, MonitorBase],
        results: Dict[str, List[RuleResult]],
    ) -> Dict:
        """
        Build complete report from monitor results.
        
        Args:
            monitors: Dictionary of monitor_name -> Monitor instance
            results: Dictionary of monitor_name -> list of rule results
            
        Returns:
            Report dictionary
        """
        # Collect all anomalies
        all_anomalies: List[RuleResult] = []
        monitor_anomalies: Dict[str, List[RuleResult]] = {}
        
        for monitor_name, monitor_results in results.items():
            anomalies = [r for r in monitor_results if r.anomaly]
            monitor_anomalies[monitor_name] = anomalies
            all_anomalies.extend(anomalies)
        
        # Calculate triage scores
        overall_score = self.scorer.score_anomalies(all_anomalies)
        monitor_scores = {}
        
        for monitor_name, anomalies in monitor_anomalies.items():
            monitor_scores[monitor_name] = self.scorer.score_anomalies(anomalies)
        
        # Ensure all monitors have scores (even if no anomalies)
        for monitor_name in monitors.keys():
            if monitor_name not in monitor_scores:
                monitor_scores[monitor_name] = self.scorer.score_anomalies([])
        
        # Collect metrics and suggested commands
        monitor_metrics = {}
        suggested_commands = []
        
        for monitor_name, monitor in monitors.items():
            if monitor.config.enabled:
                metrics = monitor.collect_metrics()
                monitor_metrics[monitor_name] = metrics
                suggested_commands.extend(monitor.get_suggested_commands())
        
        return {
            "timestamp": self._get_timestamp(),
            "overall": {
                "triage_score": overall_score.model_dump(),
                "anomaly_count": len(all_anomalies),
            },
            "monitors": {
                name: {
                    "triage_score": monitor_scores.get(name, self.scorer.score_anomalies([])).model_dump(),
                    "metrics": monitor_metrics.get(name, {}),
                    "results": [r.model_dump() for r in results.get(name, [])],
                    "anomalies": [r.model_dump() for r in monitor_anomalies.get(name, [])],
                    "suggested_commands": monitor.get_suggested_commands(),
                }
                for name, monitor in monitors.items()
            },
            "suggested_commands": list(set(suggested_commands)),  # Deduplicate
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from ..util.time import now_iso
        return now_iso()
