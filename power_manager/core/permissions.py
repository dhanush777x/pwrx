"""Permission detection and guidance helpers."""

from __future__ import annotations

import os
import subprocess


def is_root() -> bool:
    """Check if the process is running as root."""
    return os.geteuid() == 0


def can_sudo_nopass() -> bool:
    """Check if sudo -n is available (no password required)."""
    try:
        result = subprocess.run(
            ["sudo", "-n", "true"],
            capture_output=True,
            timeout=3,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


def get_privilege_message(action: str) -> str:
    """Return a user-friendly message for actions needing elevated privileges."""
    return (
        f"'{action}' requires sudo privileges.\n"
        "Run: sudo tee <path> or configure sudoers for passwordless access."
    )
