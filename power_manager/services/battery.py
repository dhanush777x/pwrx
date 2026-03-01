"""Battery statistics service."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from power_manager.core.utils import read_sysfs
from power_manager.config import POWER_SUPPLY_BASE


@dataclass
class BatteryStats:
    """Snapshot of a single battery's state."""

    name: str
    present: bool = False
    status: str = "Unknown"
    capacity: Optional[int] = None
    energy_now: Optional[int] = None        # µWh
    energy_full: Optional[int] = None       # µWh
    energy_full_design: Optional[int] = None  # µWh
    health_percent: Optional[float] = None
    ac_online: Optional[bool] = None


def get_battery_stats(battery_path: Path) -> BatteryStats:
    """Read all available stats from a battery sysfs path."""
    name = battery_path.name

    if not battery_path.exists():
        return BatteryStats(name=name, present=False)

    def _read_int(filename: str) -> Optional[int]:
        raw = read_sysfs(battery_path / filename)
        try:
            return int(raw) if raw is not None else None
        except ValueError:
            return None

    status = read_sysfs(battery_path / "status") or "Unknown"
    capacity = _read_int("capacity")
    energy_now = _read_int("energy_now")
    energy_full = _read_int("energy_full")
    energy_full_design = _read_int("energy_full_design")

    health = _calc_health(energy_full, energy_full_design)
    ac_online = _read_ac_status()

    return BatteryStats(
        name=name,
        present=True,
        status=status,
        capacity=capacity,
        energy_now=energy_now,
        energy_full=energy_full,
        energy_full_design=energy_full_design,
        health_percent=health,
        ac_online=ac_online,
    )


def _calc_health(full: Optional[int], design: Optional[int]) -> Optional[float]:
    """Calculate battery health as a percentage."""
    if full is None or design is None or design == 0:
        return None
    return round((full / design) * 100, 1)


def _read_ac_status() -> Optional[bool]:
    """Read AC adapter online status from any AC supply."""
    base = Path(POWER_SUPPLY_BASE)
    if not base.exists():
        return None
    for entry in base.iterdir():
        type_val = read_sysfs(entry / "type") or ""
        if type_val.lower() == "mains":
            online = read_sysfs(entry / "online")
            if online is not None:
                return online.strip() == "1"
    return None
