"""Triage scoring models."""

from typing import Literal
from pydantic import BaseModel

Severity = Literal["low", "medium", "high", "critical"]


class TriageScore(BaseModel):
    """Triage score for a monitor or overall system."""
    
    severity: Severity
    score: int  # 0-100
    factors: list[str] = []  # List of contributing factors
