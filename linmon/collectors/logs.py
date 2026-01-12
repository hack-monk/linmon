"""Collector for kernel logs (journald and file fallback)."""

import re
from typing import List, Optional, Tuple
from pathlib import Path
from ..util.shell import safe_subprocess, which
from ..state.model import LogCursor


class LogCollector:
    """Collects kernel logs for hung task detection."""
    
    HUNG_TASK_PATTERN = re.compile(
        r"blocked for more than (\d+) seconds",
        re.IGNORECASE
    )
    
    def __init__(self):
        """Initialize collector."""
        self.journalctl_path = which("journalctl")
        self.kernel_log_paths = [
            "/var/log/kern.log",
            "/var/log/messages",
            "/var/log/syslog",
        ]
    
    def collect_from_journald(self, cursor: Optional[str] = None) -> Tuple[List[str], Optional[str]]:
        """
        Collect kernel logs from journald.
        
        Args:
            cursor: Last journald cursor (None for first run)
            
        Returns:
            Tuple of (log_lines, new_cursor)
        """
        if not self.journalctl_path:
            return ([], None)
        
        cmd = [self.journalctl_path, "-k", "--no-pager", "-o", "short-iso"]
        
        if cursor:
            cmd.extend(["--after-cursor", cursor])
        else:
            cmd.extend(["--since", "1 hour ago"])
        
        returncode, stdout, stderr = safe_subprocess(cmd, timeout=5.0)
        
        if returncode != 0 or not stdout:
            return ([], None)
        
        lines = stdout.strip().split("\n")
        
        # Extract new cursor from last line if available
        new_cursor = None
        if lines and "cursor:" in lines[-1]:
            # Try to get cursor from journalctl output
            # Note: journalctl doesn't output cursor by default, would need --show-cursor
            pass
        
        # Try to get cursor explicitly
        cmd_cursor = [self.journalctl_path, "-k", "--show-cursor", "-n", "1"]
        returncode_cursor, stdout_cursor, _ = safe_subprocess(cmd_cursor, timeout=2.0)
        if returncode_cursor == 0 and stdout_cursor:
            for line in stdout_cursor.split("\n"):
                if line.startswith("-- cursor:"):
                    new_cursor = line.split(":", 1)[1].strip()
                    break
        
        return (lines, new_cursor)
    
    def collect_from_file(
        self,
        filepath: str,
        offset: int = 0
    ) -> Tuple[List[str], int]:
        """
        Collect kernel logs from file.
        
        Args:
            filepath: Path to log file
            offset: Byte offset to start reading from
            
        Returns:
            Tuple of (log_lines, new_offset)
        """
        path = Path(filepath)
        if not path.exists():
            return ([], offset)
        
        try:
            with open(path, "r", errors="ignore") as f:
                f.seek(offset)
                lines = f.readlines()
                new_offset = f.tell()
            
            return (lines, new_offset)
        except Exception:
            return ([], offset)
    
    def collect_kernel_logs(
        self,
        cursor: Optional[LogCursor] = None
    ) -> Tuple[List[str], Optional[LogCursor]]:
        """
        Collect kernel logs, preferring journald with file fallback.
        
        Args:
            cursor: Previous log cursor state
            
        Returns:
            Tuple of (log_lines, new_cursor)
        """
        # Try journald first
        journald_cursor = cursor.journald_cursor if cursor else None
        lines, new_journald_cursor = self.collect_from_journald(journald_cursor)
        
        if lines or new_journald_cursor:
            new_cursor = LogCursor(
                journald_cursor=new_journald_cursor,
                file_offset=cursor.file_offset if cursor else 0,
            )
            return (lines, new_cursor)
        
        # Fallback to file logs
        file_offset = cursor.file_offset if cursor else 0
        all_lines = []
        max_offset = file_offset
        
        for log_path in self.kernel_log_paths:
            path_lines, new_offset = self.collect_from_file(log_path, file_offset)
            all_lines.extend(path_lines)
            max_offset = max(max_offset, new_offset)
        
        new_cursor = LogCursor(
            journald_cursor=None,
            file_offset=max_offset,
        )
        
        return (all_lines, new_cursor)
    
    def find_hung_tasks(self, log_lines: List[str]) -> int:
        """
        Count hung task messages in log lines.
        
        Args:
            log_lines: List of log line strings
            
        Returns:
            Count of hung task detections
        """
        count = 0
        for line in log_lines:
            if self.HUNG_TASK_PATTERN.search(line):
                count += 1
        return count
