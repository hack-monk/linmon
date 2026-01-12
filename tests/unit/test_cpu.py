"""Tests for CPU monitor."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from linmon.monitors.cpu import CPUMonitor
from linmon.config.schema import CPUConfig
from linmon.rules.engine import RuleEngine
from linmon.state.manager import StateManager
import tempfile


@pytest.fixture
def state_manager():
    """Create a temporary state manager."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        state_file = f.name
    
    manager = StateManager(state_file)
    yield manager
    
    import os
    try:
        os.unlink(state_file)
    except:
        pass


@pytest.fixture
def rule_engine(state_manager):
    """Create a rule engine."""
    return RuleEngine(state_manager)


@pytest.fixture
def cpu_config():
    """Create CPU config."""
    return CPUConfig(
        enabled=True,
        sample_seconds=0.1,  # Short for testing
        rules=[],
    )


@pytest.fixture
def cpu_monitor(cpu_config, rule_engine):
    """Create CPU monitor."""
    return CPUMonitor(cpu_config, rule_engine)


def test_cpu_monitor_collect_metrics(cpu_monitor):
    """Test CPU metric collection."""
    # This will actually read from /proc on the host
    # In a real test environment, we'd mock this
    metrics = cpu_monitor.collect_metrics()
    
    # Should have at least some metrics
    assert isinstance(metrics, dict)
    # May or may not have cpu_percent depending on /proc availability
    # But should have loadavg if /proc/loadavg exists


def test_cpu_monitor_suggested_commands(cpu_monitor):
    """Test suggested commands."""
    commands = cpu_monitor.get_suggested_commands()
    assert isinstance(commands, list)
    assert len(commands) > 0
    assert all(isinstance(cmd, str) for cmd in commands)


@patch("linmon.collectors.procfs.ProcFSCollector.read_stat")
@patch("linmon.collectors.procfs.ProcFSCollector.read_loadavg")
def test_cpu_monitor_with_mocks(mock_loadavg, mock_stat, cpu_monitor):
    """Test CPU monitor with mocked collectors."""
    # Mock /proc/stat readings
    mock_stat.side_effect = [
        {"user": 100, "nice": 0, "system": 50, "idle": 1000, "iowait": 0, "irq": 0, "softirq": 0},
        {"user": 200, "nice": 0, "system": 100, "idle": 2000, "iowait": 0, "irq": 0, "softirq": 0},
    ]
    
    mock_loadavg.return_value = {"load1": 1.5, "load5": 1.2, "load15": 1.0}
    
    # This will call get_cpu_percent which needs time.sleep
    # For unit tests, we can just check that it doesn't crash
    with patch("time.sleep"):
        metrics = cpu_monitor.collect_metrics()
        assert "load1" in metrics
        assert metrics["load1"] == 1.5
