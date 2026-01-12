"""Comparison operators for rule evaluation."""

from typing import Literal

Operator = Literal["gt", "gte", "lt", "lte", "eq", "ne"]


def apply_operator(op: Operator, value: float, threshold: float) -> bool:
    """
    Apply comparison operator.
    
    Args:
        op: Operator name
        value: Actual metric value
        threshold: Threshold value
        
    Returns:
        True if condition is met (violation)
    """
    if op == "gt":
        return value > threshold
    elif op == "gte":
        return value >= threshold
    elif op == "lt":
        return value < threshold
    elif op == "lte":
        return value <= threshold
    elif op == "eq":
        return abs(value - threshold) < 1e-9  # Float comparison
    elif op == "ne":
        return abs(value - threshold) >= 1e-9
    else:
        raise ValueError(f"Unknown operator: {op}")
