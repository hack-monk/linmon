"""Tests for storage monitor."""

import pytest
import os
from unittest.mock import patch, MagicMock
from linmon.monitors.storage import StorageMonitor
from linmon.config.schema import StorageConfig, StorageMountConfig
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
def storage_config():
    """Create storage config."""
    return StorageConfig(
        enabled=True,
        mountpoints=[
            StorageMountConfig(path="/", rules=[]),
        ],
    )


@pytest.fixture
def storage_monitor(storage_config, rule_engine):
    """Create storage monitor."""
    return StorageMonitor(storage_config, rule_engine)


def test_storage_monitor_collect_metrics(storage_monitor):
    """Test storage metric collection."""
    # This will actually read from the filesystem
    metrics = storage_monitor.collect_metrics()
    
    # Should have metrics for root mountpoint
    assert isinstance(metrics, dict)
    # May have metrics if / is accessible
    if metrics:
        assert any("bytes" in key or "inodes" in key for key in metrics)


def test_storage_monitor_suggested_commands(storage_monitor):
    """Test suggested commands."""
    commands = storage_monitor.get_suggested_commands()
    assert isinstance(commands, list)
    assert len(commands) > 0


@patch("os.statvfs")
def test_storage_monitor_with_mock(mock_statvfs, storage_monitor):
    """Test storage monitor with mocked statvfs."""
    # Mock statvfs result
    mock_stat = MagicMock()
    mock_stat.f_blocks = 1000000
    mock_stat.f_bavail = 200000
    mock_stat.f_frsize = 4096
    mock_stat.f_files = 100000
    mock_stat.f_favail = 50000
    mock_statvfs.return_value = mock_stat
    
    metrics = storage_monitor.collect_metrics()
    
    # Should have calculated metrics
    assert "bytes_used_percent" in metrics
    assert metrics["bytes_used_percent"] > 0
    assert "inodes_used_percent" in metrics
