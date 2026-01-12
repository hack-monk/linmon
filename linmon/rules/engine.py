"""Rule evaluation engine with streak tracking."""

from typing import Dict, List
from .model import RuleResult
from .operators import apply_operator
from ..config.schema import Rule
from ..state.manager import StateManager


class RuleEngine:
    """Evaluates rules against metrics with streak tracking."""
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize rule engine.
        
        Args:
            state_manager: State manager for streak tracking
        """
        self.state = state_manager
    
    def evaluate(
        self,
        rules: List[Rule],
        metrics: Dict[str, float],
    ) -> List[RuleResult]:
        """
        Evaluate rules against metrics.
        
        Args:
            rules: List of rules to evaluate
            metrics: Dictionary of metric_name -> value
            
        Returns:
            List of rule evaluation results
        """
        results = []
        
        for rule in rules:
            if rule.metric not in metrics:
                # Metric not available, skip rule
                continue
            
            value = metrics[rule.metric]
            violated = apply_operator(rule.op, value, rule.value)
            
            # Update streak
            if violated:
                streak = self.state.increment_rule_streak(rule.name)
            else:
                self.state.reset_rule_streak(rule.name)
                streak = 0
            
            anomaly = streak >= rule.consecutive
            
            results.append(
                RuleResult(
                    rule_name=rule.name,
                    metric=rule.metric,
                    value=value,
                    threshold=rule.value,
                    operator=rule.op,
                    violated=violated,
                    streak=streak,
                    consecutive_required=rule.consecutive,
                    anomaly=anomaly,
                )
            )
        
        return results
