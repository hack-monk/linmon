"""Tests for rule evaluation engine."""

import pytest
from linmon.rules.engine import RuleEngine
from linmon.rules.operators import apply_operator
from linmon.rules.model import RuleResult
from linmon.config.schema import Rule
from linmon.state.manager import StateManager
import tempfile
import json


@pytest.fixture
def state_manager():
    """Create a temporary state manager."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        state_file = f.name
    
    manager = StateManager(state_file)
    yield manager
    
    # Cleanup
    import os
    try:
        os.unlink(state_file)
    except:
        pass


@pytest.fixture
def rule_engine(state_manager):
    """Create a rule engine."""
    return RuleEngine(state_manager)


def test_apply_operator_gt():
    """Test greater-than operator."""
    assert apply_operator("gt", 10.0, 5.0) is True
    assert apply_operator("gt", 5.0, 10.0) is False
    assert apply_operator("gt", 5.0, 5.0) is False


def test_apply_operator_gte():
    """Test greater-than-or-equal operator."""
    assert apply_operator("gte", 10.0, 5.0) is True
    assert apply_operator("gte", 5.0, 5.0) is True
    assert apply_operator("gte", 5.0, 10.0) is False


def test_apply_operator_lt():
    """Test less-than operator."""
    assert apply_operator("lt", 5.0, 10.0) is True
    assert apply_operator("lt", 10.0, 5.0) is False
    assert apply_operator("lt", 5.0, 5.0) is False


def test_apply_operator_lte():
    """Test less-than-or-equal operator."""
    assert apply_operator("lte", 5.0, 10.0) is True
    assert apply_operator("lte", 5.0, 5.0) is True
    assert apply_operator("lte", 10.0, 5.0) is False


def test_apply_operator_eq():
    """Test equality operator."""
    assert apply_operator("eq", 5.0, 5.0) is True
    assert apply_operator("eq", 5.0, 5.1) is False


def test_apply_operator_ne():
    """Test not-equal operator."""
    assert apply_operator("ne", 5.0, 5.1) is True
    assert apply_operator("ne", 5.0, 5.0) is False


def test_rule_engine_evaluate(rule_engine):
    """Test rule evaluation."""
    rules = [
        Rule(
            name="high_cpu",
            metric="cpu_percent",
            op="gt",
            value=80.0,
            consecutive=2,
        ),
    ]
    
    metrics = {"cpu_percent": 90.0}
    results = rule_engine.evaluate(rules, metrics)
    
    assert len(results) == 1
    assert results[0].violated is True
    assert results[0].streak == 1
    assert results[0].anomaly is False  # Not enough consecutive violations yet


def test_rule_engine_streak(rule_engine):
    """Test streak tracking."""
    rules = [
        Rule(
            name="high_cpu",
            metric="cpu_percent",
            op="gt",
            value=80.0,
            consecutive=2,
        ),
    ]
    
    metrics = {"cpu_percent": 90.0}
    
    # First violation
    results1 = rule_engine.evaluate(rules, metrics)
    assert results1[0].streak == 1
    assert results1[0].anomaly is False
    
    # Second violation (consecutive)
    results2 = rule_engine.evaluate(rules, metrics)
    assert results2[0].streak == 2
    assert results2[0].anomaly is True  # Now an anomaly
    
    # Reset when not violated
    metrics = {"cpu_percent": 50.0}
    results3 = rule_engine.evaluate(rules, metrics)
    assert results3[0].violated is False
    assert results3[0].streak == 0
