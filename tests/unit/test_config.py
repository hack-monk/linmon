"""Tests for configuration loading and validation."""

import pytest
import tempfile
import yaml
from pathlib import Path
from linmon.config.loader import load_config
from linmon.config.schema import Config, Rule, CPUConfig


def test_load_valid_config():
    """Test loading a valid configuration."""
    config_data = {
        "state_file": "/tmp/state.json",
        "report_dir": "/tmp/reports",
        "alerts": {
            "stdout": True,
            "file": "/tmp/alerts.log",
        },
        "monitors": {
            "cpu": {
                "enabled": True,
                "sample_seconds": 2.0,
                "rules": [
                    {
                        "name": "high_cpu",
                        "metric": "cpu_percent",
                        "op": "gt",
                        "value": 80.0,
                        "consecutive": 2,
                    }
                ],
            },
        },
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        config = load_config(config_path)
        assert isinstance(config, Config)
        assert config.state_file == "/tmp/state.json"
        assert config.monitors["cpu"].enabled is True
        assert len(config.monitors["cpu"].rules) == 1
    finally:
        Path(config_path).unlink()


def test_load_invalid_monitor():
    """Test that invalid monitor names are rejected."""
    config_data = {
        "monitors": {
            "invalid_monitor": {
                "enabled": True,
            },
        },
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        config_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Unknown monitor"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_rule_validation():
    """Test rule validation."""
    rule = Rule(
        name="test",
        metric="cpu_percent",
        op="gt",
        value=80.0,
        consecutive=2,
    )
    assert rule.name == "test"
    assert rule.consecutive >= 1
    
    with pytest.raises(ValueError):
        Rule(
            name="test",
            metric="cpu_percent",
            op="gt",
            value=80.0,
            consecutive=0,  # Invalid
        )
