"""Tests for IO-stuck monitor."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from linmon.monitors.iostuck import IOStuckMonitor
from linmon.config.schema import IOStuckConfig
from linmon.rules.engine import RuleEngine
from linmon.state.manager import StateManager
from linmon.state.model import LogCursor
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
def iostuck_config():
    """Create IO-stuck config."""
    return IOStuckConfig(
        enabled=True,
        rules=[],
    )


@pytest.fixture
def iostuck_monitor(iostuck_config, rule_engine, state_manager):
    """Create IO-stuck monitor."""
    return IOStuckMonitor(iostuck_config, rule_engine, state_manager)


def test_iostuck_monitor_suggested_commands(iostuck_monitor):
    """Test suggested commands."""
    commands = iostuck_monitor.get_suggested_commands()
    assert isinstance(commands, list)
    assert len(commands) > 0


@patch("linmon.collectors.logs.LogCollector.collect_kernel_logs")
@patch("linmon.collectors.logs.LogCollector.find_hung_tasks")
@patch("linmon.collectors.psi.PSICollector.is_available")
@patch("linmon.collectors.processes.ProcessCollector.get_d_state_tasks")
def test_iostuck_monitor_with_mocks(
    mock_d_state,
    mock_psi_available,
    mock_find_hung,
    mock_collect_logs,
    iostuck_monitor,
):
    """Test IO-stuck monitor with mocked collectors."""
    # Mock log collection
    mock_collect_logs.return_value = (["line1", "line2"], LogCursor(journald_cursor="cursor123"))
    mock_find_hung.return_value = 2
    
    # Mock PSI
    mock_psi_available.return_value = False
    
    # Mock D-state tasks
    mock_d_state.return_value = [
        {"pid": "1234", "state": "D", "comm": "test", "wchan": "wait"},
    ]
    
    metrics = iostuck_monitor.collect_metrics()
    
    assert "hung_task_count" in metrics
    assert metrics["hung_task_count"] == 2.0
    assert "d_state_task_count" in metrics
    assert metrics["d_state_task_count"] == 1.0


def test_log_collector_hung_task_pattern():
    """Test hung task pattern matching."""
    from linmon.collectors.logs import LogCollector
    
    collector = LogCollector()
    
    lines = [
        "INFO: task test:1234 blocked for more than 120 seconds.",
        "INFO: task test:5678 blocked for more than 60 seconds.",
        "Normal log message",
    ]
    
    count = collector.find_hung_tasks(lines)
    assert count == 2
