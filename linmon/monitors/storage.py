"""Storage usage monitor."""

import os
from typing import Dict, List
from ..monitors.base import MonitorBase
from ..config.schema import StorageConfig, StorageMountConfig


class StorageMonitor(MonitorBase):
    """Monitors disk space and inode usage."""
    
    def __init__(self, config: StorageConfig, rule_engine):
        """Initialize storage monitor."""
        super().__init__("storage", config, rule_engine)
        self.config: StorageConfig = config
    
    def collect_metrics(self) -> Dict[str, float]:
        """Collect storage metrics for all mountpoints."""
        metrics = {}
        
        for mount in self.config.mountpoints:
            # Create safe prefix from mountpoint path
            safe_path = mount.path.strip('/').replace('/', '_').replace('-', '_')
            if safe_path:
                prefix = f"mount_{safe_path}"
            else:
                prefix = "mount_root"
            
            try:
                stat = os.statvfs(mount.path)
                
                # Bytes
                total_bytes = stat.f_blocks * stat.f_frsize
                free_bytes = stat.f_bavail * stat.f_frsize
                used_bytes = total_bytes - free_bytes
                used_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0.0
                
                # Inodes
                total_inodes = stat.f_files
                free_inodes = stat.f_favail
                used_inodes = total_inodes - free_inodes
                used_inodes_percent = (used_inodes / total_inodes * 100) if total_inodes > 0 else 0.0
                
                metrics[f"{prefix}_bytes_total"] = float(total_bytes)
                metrics[f"{prefix}_bytes_free"] = float(free_bytes)
                metrics[f"{prefix}_bytes_used"] = float(used_bytes)
                metrics[f"{prefix}_bytes_used_percent"] = used_percent
                metrics[f"{prefix}_inodes_total"] = float(total_inodes)
                metrics[f"{prefix}_inodes_free"] = float(free_inodes)
                metrics[f"{prefix}_inodes_used"] = float(used_inodes)
                metrics[f"{prefix}_inodes_used_percent"] = used_inodes_percent
                
                # Also add simplified names for root mountpoint
                if mount.path == "/":
                    metrics["bytes_total"] = float(total_bytes)
                    metrics["bytes_free"] = float(free_bytes)
                    metrics["bytes_used"] = float(used_bytes)
                    metrics["bytes_used_percent"] = used_percent
                    metrics["inodes_total"] = float(total_inodes)
                    metrics["inodes_free"] = float(free_inodes)
                    metrics["inodes_used"] = float(used_inodes)
                    metrics["inodes_used_percent"] = used_inodes_percent
                    
            except (OSError, ValueError):
                # Mountpoint not accessible, skip
                continue
        
        return metrics
    
    def _get_additional_rules(self) -> List:
        """Get mountpoint-specific rules."""
        rules = []
        for mount in self.config.mountpoints:
            rules.extend(mount.rules)
        return rules
    
    def get_suggested_commands(self) -> List[str]:
        """Get suggested diagnostic commands."""
        return [
            "df -h",
            "df -i",
            "du -sh /* 2>/dev/null | sort -h | tail -10",
            "lsof +D / | head -20",
        ]
