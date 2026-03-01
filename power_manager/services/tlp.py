"""TLP power profile management service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from power_manager.core.utils import is_command_available, run_command


@dataclass
class TlpStatus:
    available:   bool          = False
    active_mode: Optional[str] = None
    error:       Optional[str] = None


def get_tlp_status() -> TlpStatus:
    if not is_command_available("tlp"):
        return TlpStatus(available=False, error="TLP is not installed")
    return TlpStatus(available=True, active_mode=_read_active_mode())


def set_tlp_profile(profile: str) -> tuple[bool, str]:
    """Run 'sudo -n tlp <profile>'. Needs NOPASSWD in sudoers."""
    if not is_command_available("tlp"):
        return False, "TLP is not installed"

    _, tlp_bin = run_command(["which", "tlp"])
    tlp_bin = tlp_bin.strip() or "/usr/bin/tlp"

    success, output = run_command(["sudo", "-n", tlp_bin, profile], timeout=15)
    if success:
        return True, f"✓ Switched to '{profile}'"

    if not output or "password" in output.lower() or "sudo:" in output.lower():
        return False, (
            f"Needs sudo — run once in terminal:  sudo tlp {profile}\n"
            f"Or add to sudoers:  %wheel ALL=(ALL) NOPASSWD: {tlp_bin}"
        )
    return False, output


# Patterns tried in order against every line of tlp-stat -s output.
# Your system outputs:  "Power profile  = performance/AC"
# Others may output:    "Power source   = AC"  or  "Mode           = auto"
_PATTERNS = [
    re.compile(r"^\s*Power profile\s*=\s*(.+)", re.IGNORECASE),
    re.compile(r"^\s*Power source\s*=\s*(.+)", re.IGNORECASE),
    re.compile(r"^\s*Mode\s*=\s*(.+)",          re.IGNORECASE),
]


def _read_active_mode() -> Optional[str]:
    """
    Parse the active TLP mode from tlp-stat -s.
    Handles all known output formats:
      Power profile  = performance/AC   → "performance/AC"
      Power source   = AC               → "AC"
      Mode           = auto             → "auto"
    """
    success, output = run_command(["tlp-stat", "-s"])
    if not success or not output:
        return None

    for line in output.splitlines()[:20]:
        for pattern in _PATTERNS:
            m = pattern.match(line)
            if m:
                return m.group(1).strip()

    return None
