"""Hardware detection: vendor, VM, batteries."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from power_manager.core.utils import read_sysfs
from power_manager.config import DMI_VENDOR_PATH, POWER_SUPPLY_BASE


@dataclass
class HardwareInfo:
    """Detected hardware properties."""

    vendor: str = "Unknown"
    is_lenovo: bool = False
    is_vm: bool = False
    battery_paths: list[Path] = field(default_factory=list)


def detect_hardware() -> HardwareInfo:
    """Detect vendor, VM state, and available batteries."""
    vendor = read_sysfs(DMI_VENDOR_PATH) or "Unknown"
    is_lenovo = "lenovo" in vendor.lower()

    batteries = _find_batteries()
    is_vm = _detect_vm(vendor)

    return HardwareInfo(
        vendor=vendor,
        is_lenovo=is_lenovo,
        is_vm=is_vm,
        battery_paths=batteries,
    )


def _find_batteries() -> list[Path]:
    """Discover all battery power supply paths."""
    base = Path(POWER_SUPPLY_BASE)
    if not base.exists():
        return []
    return [
        entry
        for entry in sorted(base.iterdir())
        if (entry / "type").exists()
        and (read_sysfs(entry / "type") or "").lower() == "battery"
    ]


def _detect_vm(vendor: str) -> bool:
    """Heuristic VM detection based on vendor string."""
    vm_keywords = ("vmware", "virtualbox", "qemu", "kvm", "xen", "hyper-v", "innotek")
    return any(kw in vendor.lower() for kw in vm_keywords)
