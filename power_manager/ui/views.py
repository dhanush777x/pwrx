"""
Views for Linux Power Manager.

All colours via var(--pm-*) — defined once in app.py Screen block.
No hardcoded hex, no Textual $vars here.

Quadrant layout:
  ┌──────────────┬──────────────┐
  │   Battery    │     TLP      │
  ├──────────────┼──────────────┤
  │     CPU      │ Conservation │
  └──────────────┴──────────────┘
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from power_manager.ui.widgets import ErrorBanner, InfoBanner, SectionHeader, StatusRow
from power_manager.services.battery import BatteryStats
from power_manager.services.tlp import TlpStatus
from power_manager.services.conservation import ConservationStatus
from power_manager.services.cpu import CpuStats
from power_manager.config import TLP_PROFILES


# ── Battery ───────────────────────────────────────────────────────────────────

class BatteryView(Widget):
    DEFAULT_CSS = """
    BatteryView { padding: 0 0 1 0; }
    """

    def compose(self) -> ComposeResult:
        yield SectionHeader("⚡  Battery")
        yield StatusRow("Status",            id="bat-status")
        yield StatusRow("Charge",            id="bat-charge")
        yield StatusRow("Health",            id="bat-health")
        yield StatusRow("Energy Now / Full", id="bat-energy")
        yield StatusRow("AC Connected",      id="bat-ac")

    def refresh_stats(self, stats_list: list[BatteryStats]) -> None:
        if not stats_list:
            self._blank("No battery detected"); return
        s = stats_list[0]
        if not s.present:
            self._blank("Battery not present"); return
        self.query_one("#bat-status", StatusRow).update_value(_fmt_status(s.status))
        self.query_one("#bat-charge", StatusRow).update_value(
            f"{s.capacity}%" if s.capacity is not None else "—")
        self.query_one("#bat-health", StatusRow).update_value(
            f"{s.health_percent:.1f}%" if s.health_percent is not None else "—")
        energy = "—"
        if s.energy_full is not None and s.energy_full_design is not None:
            energy = f"{s.energy_full // 1000} / {s.energy_full_design // 1000} mWh"
        self.query_one("#bat-energy", StatusRow).update_value(energy)
        self.query_one("#bat-ac", StatusRow).update_value(
            ("Yes" if s.ac_online else "No") if s.ac_online is not None else "—")

    def _blank(self, msg: str) -> None:
        self.query_one("#bat-status", StatusRow).update_value(msg)
        for r in ("#bat-charge", "#bat-health", "#bat-energy", "#bat-ac"):
            self.query_one(r, StatusRow).update_value("—")


# ── CPU ───────────────────────────────────────────────────────────────────────

class CpuView(Widget):
    DEFAULT_CSS = """
    CpuView { padding: 0 0 1 0; }
    """

    def compose(self) -> ComposeResult:
        yield SectionHeader("🖥   CPU Stats")
        yield StatusRow("Usage",       id="cpu-usage")
        yield StatusRow("Frequency",   id="cpu-freq")
        yield StatusRow("Governor",    id="cpu-gov")
        yield StatusRow("Temperature", id="cpu-temp")

    def refresh_stats(self, stats: CpuStats) -> None:
        self.query_one("#cpu-usage", StatusRow).update_value(
            f"{stats.usage_percent:.1f}%")
        self.query_one("#cpu-freq",  StatusRow).update_value(
            f"{stats.frequency_mhz:.0f} MHz" if stats.frequency_mhz else "—")
        self.query_one("#cpu-gov",   StatusRow).update_value(stats.governor or "—")
        self.query_one("#cpu-temp",  StatusRow).update_value(
            f"{stats.temperature_c}°C" if stats.temperature_c is not None else "—")


# ── TLP ───────────────────────────────────────────────────────────────────────

class TlpView(Widget):
    """
    j/k   — move cursor up/down
    Enter — apply selected profile
    1-5   — jump directly to profile (handled by app)
    """

    DEFAULT_CSS = """
    TlpView { padding: 0 0 1 0; }
    """

    _cursor:    int  = 0
    _available: bool = False

    def compose(self) -> ComposeResult:
        yield SectionHeader("⚙   TLP Power Profile")
        yield StatusRow("Status",  id="tlp-status")
        yield StatusRow("Current", id="tlp-current")
        yield Static(" ", id="tlp-gap")
        for i, profile in enumerate(TLP_PROFILES, 1):
            yield Static(
                f"   [{i}]  {profile.capitalize():<14}",
                id=f"tlp-p-{profile}",
                classes="profile-row",
            )
        yield Static(" ", id="tlp-gap2")
        yield ErrorBanner(id="tlp-error")
        yield InfoBanner(id="tlp-info")

    def on_mount(self) -> None:
        self._render_cursor()

    def refresh_stats(self, status: TlpStatus) -> None:
        self._available = status.available
        self.query_one("#tlp-status",  StatusRow).update_value(
            "Installed ✓" if status.available else "Not installed")
        self.query_one("#tlp-current", StatusRow).update_value(
            status.active_mode or "—")
        if not status.available and status.error:
            self.query_one("#tlp-error", ErrorBanner).show(status.error)
        # "performance/AC" → extract just "performance" before any "/"
        active_raw = (status.active_mode or "").strip().lower().split("/")[0].strip()
        for profile in TLP_PROFILES:
            row = self.query_one(f"#tlp-p-{profile}", Static)
            p = profile.lower()
            # exact match or profile is a prefix word of active_raw
            matched = active_raw == p or active_raw.startswith(p + "-") or active_raw.startswith(p + "_")
            if active_raw and matched:
                row.add_class("active")
            else:
                row.remove_class("active")
        self._render_cursor()

    def move_cursor(self, delta: int) -> None:
        self._cursor = (self._cursor + delta) % len(TLP_PROFILES)
        self._render_cursor()

    def set_cursor(self, idx: int) -> None:
        if 0 <= idx < len(TLP_PROFILES):
            self._cursor = idx
            self._render_cursor()

    def selected_profile(self) -> Optional[str]:
        return TLP_PROFILES[self._cursor] if self._available else None

    def is_available(self) -> bool:
        return self._available

    def _render_cursor(self) -> None:
        for i, profile in enumerate(TLP_PROFILES):
            try:
                row = self.query_one(f"#tlp-p-{profile}", Static)
            except Exception:
                return
            marker = "▶" if i == self._cursor else " "
            row.update(f"  {marker} [{i + 1}]  {profile.capitalize():<14}")
            if i == self._cursor:
                row.add_class("highlighted")
            else:
                row.remove_class("highlighted")

    def show_feedback(self, success: bool, message: str) -> None:
        if success:
            self.query_one("#tlp-info",  InfoBanner).show(message)
            self.query_one("#tlp-error", ErrorBanner).hide()
        else:
            self.query_one("#tlp-error", ErrorBanner).show(message)


# ── Conservation ──────────────────────────────────────────────────────────────

class ConservationView(Widget):
    DEFAULT_CSS = """
    ConservationView { padding: 0 0 1 0; }
    """

    _enabled:   Optional[bool] = None
    _supported: bool           = False

    def compose(self) -> ComposeResult:
        yield SectionHeader("🔋  Conservation Mode")
        yield StatusRow("Support", id="cons-support")
        yield StatusRow("Vendor",  id="cons-vendor")
        yield Static(" ")
        yield Static("  ●  Checking…", id="cons-state")
        yield Static(" ")
        yield Static("  Press c to toggle", id="cons-hint")
        yield ErrorBanner(id="cons-error")
        yield InfoBanner(id="cons-info")

    def refresh_stats(self, status: ConservationStatus, vendor: str = "") -> None:
        self._supported = status.supported
        self._enabled   = status.enabled
        self.query_one("#cons-vendor", StatusRow).update_value(vendor or "—")
        if not status.supported:
            self.query_one("#cons-support", StatusRow).update_value("Not supported")
            st = self.query_one("#cons-state", Static)
            st.update("  ●  Unavailable on this hardware")
            st.remove_class("on", "off")
            self.query_one("#cons-hint", Static).update("")
            if status.error:
                self.query_one("#cons-error", ErrorBanner).show(status.error)
            return
        self.query_one("#cons-support", StatusRow).update_value("Supported ✓")
        self._render_state()

    def _render_state(self) -> None:
        st = self.query_one("#cons-state", Static)
        if self._enabled:
            st.update("  ●  ENABLED — charging capped to ~80%")
            st.remove_class("off"); st.add_class("on")
        else:
            st.update("  ○  DISABLED  — charges to 100%")
            st.remove_class("on"); st.add_class("off")

    def toggle(self) -> Optional[bool]:
        if not self._supported or self._enabled is None:
            return None
        return not self._enabled

    def apply_toggle(self, new_state: bool) -> None:
        self._enabled = new_state
        self._render_state()

    def show_feedback(self, success: bool, message: str) -> None:
        if success:
            self.query_one("#cons-info",  InfoBanner).show(message)
            self.query_one("#cons-error", ErrorBanner).hide()
        else:
            self.query_one("#cons-error", ErrorBanner).show(message)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_status(s: str) -> str:
    return {
        "charging":     "⚡ Charging",
        "discharging":  "🔋 Discharging",
        "full":         "✅ Full",
        "not charging": "— Not Charging",
    }.get(s.lower(), s)
