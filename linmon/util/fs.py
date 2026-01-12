"""File system utilities with atomic operations."""

import os
import tempfile
from pathlib import Path
from typing import Any
import json


def atomic_write(filepath: str, content: str, mode: str = "w") -> None:
    """
    Atomically write content to a file using a temporary file and rename.
    
    Args:
        filepath: Target file path
        content: Content to write (string)
        mode: Write mode ('w' for text, 'wb' for binary)
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary file in same directory for atomic rename
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.tmp")
    try:
        with os.fdopen(fd, mode) as f:
            f.write(content)
        # Atomic rename
        os.replace(tmp_path, path)
    except Exception:
        # Cleanup on error
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_json(filepath: str, data: Any, indent: int = 2) -> None:
    """
    Atomically write JSON data to a file.
    
    Args:
        filepath: Target file path
        data: JSON-serializable data
        indent: JSON indentation
    """
    content = json.dumps(data, indent=indent)
    atomic_write(filepath, content)


def ensure_dir(dirpath: str) -> None:
    """Ensure directory exists, creating if necessary."""
    Path(dirpath).mkdir(parents=True, exist_ok=True)
