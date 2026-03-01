"""Safe filesystem and subprocess helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def read_sysfs(path: str | Path) -> Optional[str]:
    """Safely read a sysfs file, returning None on any error."""
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except (FileNotFoundError, PermissionError, OSError):
        return None


def write_sysfs(path: str | Path, value: str) -> bool:
    """
    Write to a sysfs file.
    Tries direct write first (works if running as root or file is world-writable).
    Falls back to 'sudo -n tee' (needs NOPASSWD for tee in sudoers).
    Falls back to 'sudo tee' with a small timeout.
    """
    path = Path(path)

    # 1. Direct write (works if user has write permission)
    try:
        path.write_text(value, encoding="utf-8")
        return True
    except PermissionError:
        pass
    except OSError:
        pass

    # 2. sudo -n tee (non-interactive, needs sudoers NOPASSWD)
    try:
        result = subprocess.run(
            ["sudo", "-n", "tee", str(path)],
            input=value,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass

    # 3. pkexec tee (graphical polkit prompt — silent fallback)
    try:
        result = subprocess.run(
            ["pkexec", "tee", str(path)],
            input=value,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass

    return False


def run_command(cmd: list[str], timeout: int = 5) -> tuple[bool, str]:
    """Run a shell command. Returns (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except subprocess.SubprocessError as e:
        return False, str(e)


def is_command_available(cmd: str) -> bool:
    """Check if a CLI tool is installed."""
    success, _ = run_command(["which", cmd])
    return success
