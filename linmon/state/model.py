"""State data models."""

from typing import Dict, Optional
from pydantic import BaseModel


class RuleState(BaseModel):
    """State for a single rule (streak counter)."""
    
    streak: int = 0
    last_violation: Optional[str] = None


class LogCursor(BaseModel):
    """Log cursor state for tracking read position."""
    
    journald_cursor: Optional[str] = None
    file_offset: int = 0


class State(BaseModel):
    """Complete application state."""
    
    rule_streaks: Dict[str, int] = {}  # rule_name -> streak count
    log_cursors: Dict[str, LogCursor] = {}  # log_source -> cursor
    last_run: Optional[str] = None
