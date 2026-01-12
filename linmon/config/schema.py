"""Pydantic schemas for configuration validation."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
from .defaults import (
    DEFAULT_STATE_FILE,
    DEFAULT_REPORT_DIR,
    DEFAULT_ALERT_FILE,
    DEFAULT_CPU_SAMPLE_SECONDS,
    DEFAULT_STORAGE_MOUNTPOINTS,
)


# Valid operators
Operator = Literal["gt", "gte", "lt", "lte", "eq", "ne"]


class Rule(BaseModel):
    """Rule definition for threshold evaluation."""
    
    name: str = Field(..., description="Rule name")
    metric: str = Field(..., description="Metric name to evaluate")
    op: Operator = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value")
    consecutive: int = Field(..., ge=1, description="Number of consecutive violations required")
    args: Dict[str, Any] = Field(default_factory=dict, description="Optional rule-specific args")


class StorageMountConfig(BaseModel):
    """Storage mountpoint configuration."""
    
    path: str = Field(..., description="Mountpoint path")
    rules: List[Rule] = Field(default_factory=list, description="Rules for this mountpoint")


class MonitorConfig(BaseModel):
    """Base monitor configuration."""
    
    enabled: bool = Field(default=True, description="Whether monitor is enabled")
    rules: List[Rule] = Field(default_factory=list, description="Global rules")


class CPUConfig(MonitorConfig):
    """CPU monitor configuration."""
    
    sample_seconds: float = Field(
        default=DEFAULT_CPU_SAMPLE_SECONDS,
        ge=0.1,
        le=60.0,
        description="CPU sampling duration in seconds"
    )


class StorageConfig(MonitorConfig):
    """Storage monitor configuration."""
    
    mountpoints: List[StorageMountConfig] = Field(
        default_factory=lambda: [StorageMountConfig(path=p) for p in DEFAULT_STORAGE_MOUNTPOINTS],
        description="Mountpoints to monitor"
    )


class IOStuckConfig(MonitorConfig):
    """IO-stuck monitor configuration."""
    
    pass


class AlertsConfig(BaseModel):
    """Alerting configuration."""
    
    stdout: bool = Field(default=True, description="Enable stdout alerts")
    file: Optional[str] = Field(default=DEFAULT_ALERT_FILE, description="File path for alerts (None to disable)")


class Config(BaseModel):
    """Root configuration schema."""
    
    state_file: str = Field(default=DEFAULT_STATE_FILE, description="State persistence file path")
    report_dir: str = Field(default=DEFAULT_REPORT_DIR, description="Report output directory")
    alerts: AlertsConfig = Field(default_factory=AlertsConfig, description="Alert configuration")
    
    monitors: Dict[str, Any] = Field(..., description="Monitor configurations")
    
    @field_validator("monitors", mode="before")
    @classmethod
    def validate_monitors(cls, v: Any) -> Dict[str, Any]:
        """Validate and parse monitor configurations."""
        if not isinstance(v, dict):
            raise ValueError("monitors must be a dictionary")
        
        result = {}
        for monitor_name, monitor_data in v.items():
            if monitor_name == "cpu":
                result[monitor_name] = CPUConfig(**monitor_data)
            elif monitor_name == "storage":
                result[monitor_name] = StorageConfig(**monitor_data)
            elif monitor_name == "iostuck":
                result[monitor_name] = IOStuckConfig(**monitor_data)
            else:
                raise ValueError(f"Unknown monitor: {monitor_name}")
        
        return result
