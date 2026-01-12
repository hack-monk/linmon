"""Rule evaluation result models."""

from typing import Optional
from pydantic import BaseModel


class RuleResult(BaseModel):
    """Result of rule evaluation."""
    
    rule_name: str
    metric: str
    value: float
    threshold: float
    operator: str
    violated: bool
    streak: int
    consecutive_required: int
    anomaly: bool  # True if streak >= consecutive_required
