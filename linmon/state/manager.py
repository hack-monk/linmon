"""State manager with atomic persistence."""

import json
from pathlib import Path
from typing import Optional
from .model import State, LogCursor
from ..util.fs import atomic_write_json, ensure_dir


class StateManager:
    """Manages state persistence with atomic writes."""
    
    def __init__(self, state_file: str):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state JSON file
        """
        self.state_file = state_file
        self._state: Optional[State] = None
    
    def load(self) -> State:
        """Load state from file, creating empty state if file doesn't exist."""
        if self._state is not None:
            return self._state
        
        path = Path(self.state_file)
        if not path.exists():
            self._state = State()
            return self._state
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            self._state = State(**data)
        except Exception:
            # On any error, start fresh
            self._state = State()
        
        return self._state
    
    def save(self) -> None:
        """Atomically save state to file."""
        if self._state is None:
            return
        
        ensure_dir(str(Path(self.state_file).parent))
        atomic_write_json(self.state_file, self._state.model_dump())
    
    def get_rule_streak(self, rule_name: str) -> int:
        """Get current streak count for a rule."""
        state = self.load()
        return state.rule_streaks.get(rule_name, 0)
    
    def increment_rule_streak(self, rule_name: str) -> int:
        """Increment streak for a rule and return new count."""
        state = self.load()
        current = state.rule_streaks.get(rule_name, 0)
        state.rule_streaks[rule_name] = current + 1
        self._state = state
        return state.rule_streaks[rule_name]
    
    def reset_rule_streak(self, rule_name: str) -> None:
        """Reset streak for a rule."""
        state = self.load()
        if rule_name in state.rule_streaks:
            del state.rule_streaks[rule_name]
        self._state = state
    
    def get_log_cursor(self, source: str) -> Optional[LogCursor]:
        """Get log cursor for a source."""
        state = self.load()
        return state.log_cursors.get(source)
    
    def set_log_cursor(self, source: str, cursor: LogCursor) -> None:
        """Set log cursor for a source."""
        state = self.load()
        state.log_cursors[source] = cursor
        self._state = state
    
    def update_last_run(self, timestamp: str) -> None:
        """Update last run timestamp."""
        state = self.load()
        state.last_run = timestamp
        self._state = state
