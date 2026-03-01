"""CPU statistics service — AMD and Intel compatible."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil

from power_manager.core.utils import read_sysfs
from power_manager.config import CPU_FREQ_BASE


@dataclass
class CpuStats:
    usage_percent: float = 0.0
    frequency_mhz: Optional[float] = None
    governor: Optional[str] = None
    temperature_c: Optional[float] = None


def prime_cpu_percent() -> None:
    """
    Call once at startup to initialise psutil's CPU measurement baseline.
    psutil.cpu_percent(interval=None) returns 0.0 on the very first call
    because it has no previous sample — this primes it so subsequent calls
    return real values instantly without any blocking sleep.
    """
    psutil.cpu_percent(interval=None)


def get_cpu_stats() -> CpuStats:
    """Collect CPU usage, frequency, governor, and temperature. Non-blocking."""
    return CpuStats(
        usage_percent=psutil.cpu_percent(interval=None),
        frequency_mhz=_read_frequency(),
        governor=_read_governor(),
        temperature_c=_read_temperature(),
    )


def _read_frequency() -> Optional[float]:
    raw = read_sysfs(Path(CPU_FREQ_BASE) / "scaling_cur_freq")
    if raw:
        try:
            return int(raw) / 1000  # kHz → MHz
        except ValueError:
            pass
    freq = psutil.cpu_freq()
    return round(freq.current, 1) if freq else None


def _read_governor() -> Optional[str]:
    return read_sysfs(Path(CPU_FREQ_BASE) / "scaling_governor")


def _read_temperature() -> Optional[float]:
    try:
        temps = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return None
    if not temps:
        return None
    for key in ["k10temp", "coretemp", "acpitz", "cpu_thermal", *temps.keys()]:
        if key in temps and temps[key]:
            return round(temps[key][0].current, 1)
    return None
