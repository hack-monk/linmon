"""Base monitor class."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from ..rules.model import RuleResult
from ..rules.engine import RuleEngine


class MonitorBase(ABC):
    """Base class for all monitors."""
    
    def __init__(self, name: str, config: Any, rule_engine: RuleEngine):
        """
        Initialize monitor.
        
        Args:
            name: Monitor name
            config: Monitor configuration
            rule_engine: Rule evaluation engine
        """
        self.name = name
        self.config = config
        self.rule_engine = rule_engine
    
    @abstractmethod
    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect metrics for this monitor.
        
        Returns:
            Dictionary of metric_name -> value
        """
        pass
    
    @abstractmethod
    def get_suggested_commands(self) -> List[str]:
        """
        Get suggested diagnostic commands for this monitor.
        
        Returns:
            List of command strings
        """
        pass
    
    def evaluate(self) -> List[RuleResult]:
        """
        Evaluate rules against collected metrics.
        
        Returns:
            List of rule evaluation results
        """
        if not self.config.enabled:
            return []
        
        metrics = self.collect_metrics()
        all_rules = list(self.config.rules)
        
        # Allow subclasses to add mountpoint-specific rules
        mountpoint_rules = self._get_additional_rules()
        all_rules.extend(mountpoint_rules)
        
        return self.rule_engine.evaluate(all_rules, metrics)
    
    def _get_additional_rules(self) -> List:
        """Override in subclasses to add mountpoint-specific rules."""
        return []
