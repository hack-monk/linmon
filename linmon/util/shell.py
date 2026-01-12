"""Safe subprocess execution utilities."""

import subprocess
import shutil
from typing import Optional, Tuple, List


def safe_subprocess(
    cmd: List[str],
    timeout: float = 10.0,
    check: bool = False,
    capture_output: bool = True,
    text: bool = True,
) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Safely execute a subprocess with timeout.
    
    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds
        check: If True, raise on non-zero exit
        capture_output: If True, capture stdout/stderr
        text: If True, return text instead of bytes
        
    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            text=text,
        )
        stdout = result.stdout if capture_output else None
        stderr = result.stderr if capture_output else None
        return (result.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        return (-1, None, f"Command timed out after {timeout}s")
    except FileNotFoundError:
        return (-1, None, f"Command not found: {cmd[0]}")
    except Exception as e:
        return (-1, None, str(e))


def which(cmd: str) -> Optional[str]:
    """Find command in PATH, similar to Unix which."""
    return shutil.which(cmd)
