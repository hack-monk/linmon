"""Base alert class."""

from abc import ABC, abstractmethod
from typing import Dict, List
from ..rules.model import RuleResult


class AlertBase(ABC):
    """Base class for alert handlers."""
    
    @abstractmethod
    def send(self, anomalies: List[RuleResult], report: Dict) -> None:
        """
        Send alert.
        
        Args:
            anomalies: List of anomaly rule results
            report: Full report dictionary
        """
        pass
