"""Lenovo conservation mode toggle service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from power_manager.core.utils import read_sysfs, write_sysfs
from power_manager.config import CONSERVATION_MODE_PATH


@dataclass
class ConservationStatus:
    """Conservation mode availability and current state."""

    supported: bool = False
    enabled: Optional[bool] = None
    error: Optional[str] = None


def get_conservation_status(is_lenovo: bool) -> ConservationStatus:
    """Read conservation mode state if hardware supports it."""
    if not is_lenovo:
        return ConservationStatus(supported=False)

    path = Path(CONSERVATION_MODE_PATH)
    if not path.exists():
        return ConservationStatus(supported=False, error="Conservation mode path not found")

    raw = read_sysfs(path)
    if raw is None:
        return ConservationStatus(supported=True, error="Cannot read conservation mode")

    try:
        enabled = int(raw) == 1
    except ValueError:
        return ConservationStatus(supported=True, error=f"Unexpected value: {raw!r}")

    return ConservationStatus(supported=True, enabled=enabled)


def set_conservation_mode(enabled: bool) -> tuple[bool, str]:
    """
    Enable or disable conservation mode.

    Returns:
        (success, message)
    """
    value = "1" if enabled else "0"
    success = write_sysfs(CONSERVATION_MODE_PATH, value)
    if success:
        state = "enabled" if enabled else "disabled"
        return True, f"Conservation mode {state}"
    return False, "Failed to write conservation mode — sudo privileges required"
