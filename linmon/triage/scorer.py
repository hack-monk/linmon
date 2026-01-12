"""Triage scoring logic."""

from typing import List
from .model import TriageScore, Severity
from ..rules.model import RuleResult


class TriageScorer:
    """Calculates triage scores based on rule violations."""
    
    @staticmethod
    def score_anomalies(anomalies: List[RuleResult]) -> TriageScore:
        """
        Calculate triage score from anomalies.
        
        Args:
            anomalies: List of rule results that are anomalies
            
        Returns:
            TriageScore with severity and score
        """
        if not anomalies:
            return TriageScore(severity="low", score=0, factors=[])
        
        # Count by severity indicators
        critical_count = 0
        high_count = 0
        medium_count = 0
        
        factors = []
        
        for anomaly in anomalies:
            # High streak indicates persistent issue
            if anomaly.streak >= 5:
                critical_count += 1
                factors.append(f"{anomaly.rule_name}: persistent (streak={anomaly.streak})")
            elif anomaly.streak >= 3:
                high_count += 1
                factors.append(f"{anomaly.rule_name}: repeated (streak={anomaly.streak})")
            else:
                medium_count += 1
                factors.append(f"{anomaly.rule_name}: threshold exceeded")
        
        # Calculate score (0-100)
        score = min(100, (critical_count * 30) + (high_count * 15) + (medium_count * 5))
        
        # Determine severity
        if critical_count > 0 or score >= 60:
            severity: Severity = "critical"
        elif high_count > 0 or score >= 40:
            severity = "high"
        elif medium_count > 0 or score >= 20:
            severity = "medium"
        else:
            severity = "low"
        
        return TriageScore(severity=severity, score=score, factors=factors)
