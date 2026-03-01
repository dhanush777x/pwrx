"""Central configuration and constants."""

from pathlib import Path

APP_NAME = "pwrx - Linux Power Manager TUI"
APP_VERSION = "1.0.0"
REFRESH_INTERVAL = 2.0  # seconds

# Sysfs paths
POWER_SUPPLY_BASE = "/sys/class/power_supply"
DMI_VENDOR_PATH   = "/sys/class/dmi/id/sys_vendor"
CPU_FREQ_BASE     = "/sys/devices/system/cpu/cpu0/cpufreq"

# TLP profiles (order matches keys 1-5)
TLP_PROFILES = ["ac", "bat", "performance", "balanced", "power-saver"]

# Log path
LOG_DIR = "~/.local/state/power-manager"

# Conservation mode — auto-discover path since VPC ID varies per machine
def _find_conservation_path() -> str:
    base = Path("/sys/bus/platform/drivers/ideapad_acpi")
    if base.exists():
        for entry in base.iterdir():
            candidate = entry / "conservation_mode"
            if candidate.exists():
                return str(candidate)
    # fallback to known common path
    return "/sys/bus/platform/drivers/ideapad_acpi/VPC2004:00/conservation_mode"

CONSERVATION_MODE_PATH: str = _find_conservation_path()
