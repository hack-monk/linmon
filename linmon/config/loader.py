"""Configuration loader with YAML parsing and validation."""

import yaml
from pathlib import Path
from typing import Optional
from .schema import Config


def load_config(config_path: str) -> Config:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Validated Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    
    if data is None:
        raise ValueError("Config file is empty")
    
    try:
        return Config(**data)
    except Exception as e:
        raise ValueError(f"Invalid config: {e}") from e
