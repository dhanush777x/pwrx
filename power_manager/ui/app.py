"""
Linux Power Manager
Default theme: Catppuccin Mocha (lavender accent)

Ctrl+T cycles through registered themes.
No command palette, no help panel noise.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Grid, Vertical
from textual.theme import Theme
from textual.widgets import Footer, Header, Label
from textual.worker import get_current_worker

from power_manager.ui.views import BatteryView, ConservationView, CpuView, TlpView
from power_manager.services.battery import get_battery_stats, BatteryStats
from power_manager.services.conservation import (
    get_conservation_status, set_conservation_mode, ConservationStatus,
)
from power_manager.services.cpu import get_cpu_stats, prime_cpu_percent, CpuStats
from power_manager.services.hardware import detect_hardware, HardwareInfo
from power_manager.services.tlp import get_tlp_status, set_tlp_profile, TlpStatus
from power_manager.config import APP_NAME, APP_VERSION, REFRESH_INTERVAL, TLP_PROFILES


# ── Themes ────────────────────────────────────────────────────────────────────

CATPPUCCIN_MOCHA = Theme(
    name="catppuccin-mocha",
    dark=True,
    background="#1e1e2e",
    surface="#313244",
    panel="#45475a",
    primary="#b4befe",
    secondary="#cba6f7",
    accent="#b4befe",
    foreground="#cdd6f4",
    success="#a6e3a1",
    warning="#f9e2af",
    error="#f38ba8",
)

CATPPUCCIN_LATTE = Theme(
    name="catppuccin-latte",
    dark=False,
    background="#eff1f5",
    surface="#e6e9ef",
    panel="#dce0e8",
    primary="#7287fd",
    secondary="#8839ef",
    accent="#7287fd",
    foreground="#4c4f69",
    success="#40a02b",
    warning="#df8e1d",
    error="#d20f39",
)

_THEMES = ["catppuccin-mocha", "catppuccin-latte"]


class PowerManagerApp(App):
    TITLE = f"{APP_NAME}  v{APP_VERSION}"
    CSS_PATH = None
    THEME = "catppuccin-mocha"

    # Disable the built-in command palette entirely
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    Screen {
        background: $background;
    }
    Header {
        background: $background;
        color: $primary;
        text-style: bold;
    }
    Footer {
        background: $surface;
        color: $text-muted;
    }
    #root {
        layout: vertical;
        padding: 0 1;
        height: 100%;
        background: $background;
    }
    #sysinfo {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    #grid {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        height: 1fr;
        margin-top: 1;
    }
    #keyhint {
        height: 1;
        color: $text-muted;
        padding: 0 1;
        margin-top: 1;
        text-align: center;
    }
    BatteryView, CpuView, TlpView, ConservationView {
        height: 100%;
        background: $background;
        border: solid $panel;
    }
    SectionHeader {
        background: $surface;
        color: $primary;
        text-style: bold;
        padding: 0 1;
    }
    StatusRow {
        height: 1;
        padding: 0 2;
        layout: horizontal;
        background: $background;
    }
    StatusRow .key   { color: $text-muted; width: 22; }
    StatusRow .value { color: $text;                  }
    .profile-row {
        height: 1;
        padding: 0 2;
        color: $text-muted;
        background: $background;
    }
    .profile-row.highlighted {
        background: $primary;
        color: $background;
        text-style: bold;
    }
    .profile-row.active {
        color: $success;
        text-style: bold;
    }
    .profile-row.highlighted.active {
        background: $primary;
        color: $background;
        text-style: bold;
    }
    #cons-state {
        height: 1;
        padding: 0 3;
        text-style: bold;
        background: $background;
    }
    #cons-state.on  { color: $success; }
    #cons-state.off { color: $error;   }
    #cons-hint {
        height: 1;
        padding: 0 3;
        color: $text-muted;
        background: $background;
    }
    ErrorBanner {
        background: $error;
        color: $background;
        padding: 0 1;
        display: none;
    }
    ErrorBanner.visible { display: block; }
    InfoBanner {
        background: $success;
        color: $background;
        padding: 0 1;
        display: none;
    }
    InfoBanner.visible { display: block; }
    """

    BINDINGS = [
        Binding("q",      "quit",              "Quit"),
        Binding("r",      "refresh",           "Refresh"),
        Binding("ctrl+t", "cycle_theme",       "Theme"),
        Binding("j",      "tlp_down",          "▼",                     show=False),
        Binding("k",      "tlp_up",            "▲",                     show=False),
        Binding("enter",  "tlp_apply",         "Apply",                 show=False),
        Binding("c",      "conservation",      "Toggle Conservation"),
        Binding("1",      "tlp_select('0')",   "",                      show=False),
        Binding("2",      "tlp_select('1')",   "",                      show=False),
        Binding("3",      "tlp_select('2')",   "",                      show=False),
        Binding("4",      "tlp_select('3')",   "",                      show=False),
        Binding("5",      "tlp_select('4')",   "",                      show=False),
        Binding("ctrl+c", "quit",                                       show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._hw: HardwareInfo = detect_hardware()

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="root"):
            yield Label(self._sysinfo_text(), id="sysinfo")
            with Grid(id="grid"):
                yield BatteryView(id="battery-view")
                yield TlpView(id="tlp-view")
                yield CpuView(id="cpu-view")
                yield ConservationView(id="conservation-view")
            yield Label(
                "j/k ▲▼  Enter apply  │  1-5 TLP  │  c conservation  │  ctrl+t theme  │  r refresh  │  q quit",
                id="keyhint",
            )
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(CATPPUCCIN_MOCHA)
        self.register_theme(CATPPUCCIN_LATTE)
        self.theme = "catppuccin-mocha"
        prime_cpu_percent()
        self._start_refresh()
        self.set_interval(REFRESH_INTERVAL, self._start_refresh)

    # ── Background refresh ────────────────────────────────────────────────────

    def _start_refresh(self) -> None:
        self.run_worker(self._fetch_all, exclusive=True, thread=True)

    def _fetch_all(self) -> None:
        worker = get_current_worker()
        battery_stats: list[BatteryStats]  = [get_battery_stats(p) for p in self._hw.battery_paths]
        tlp_status:    TlpStatus           = get_tlp_status()
        cpu_stats:     CpuStats            = get_cpu_stats()
        cons_status:   ConservationStatus  = get_conservation_status(self._hw.is_lenovo)
        if worker.is_cancelled:
            return
        self.call_from_thread(self._apply_battery,      battery_stats)
        self.call_from_thread(self._apply_tlp,          tlp_status)
        self.call_from_thread(self._apply_cpu,          cpu_stats)
        self.call_from_thread(self._apply_conservation, cons_status)

    def _apply_battery(self, stats: list[BatteryStats]) -> None:
        self.query_one("#battery-view", BatteryView).refresh_stats(stats)

    def _apply_tlp(self, status: TlpStatus) -> None:
        self.query_one("#tlp-view", TlpView).refresh_stats(status)

    def _apply_cpu(self, stats: CpuStats) -> None:
        self.query_one("#cpu-view", CpuView).refresh_stats(stats)

    def _apply_conservation(self, status: ConservationStatus) -> None:
        self.query_one("#conservation-view", ConservationView).refresh_stats(
            status, vendor=self._hw.vendor)

    # ── Key actions ───────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        self._start_refresh()

    def action_cycle_theme(self) -> None:
        """Cycle through registered themes with ctrl+t."""
        current = self.theme
        idx = _THEMES.index(current) if current in _THEMES else 0
        self.theme = _THEMES[(idx + 1) % len(_THEMES)]

    def action_tlp_down(self) -> None:
        self.query_one("#tlp-view", TlpView).move_cursor(1)

    def action_tlp_up(self) -> None:
        self.query_one("#tlp-view", TlpView).move_cursor(-1)

    def action_tlp_apply(self) -> None:
        view = self.query_one("#tlp-view", TlpView)
        self._run_tlp(view, view.selected_profile())

    def action_tlp_select(self, idx: str) -> None:
        view = self.query_one("#tlp-view", TlpView)
        i = int(idx)
        view.set_cursor(i)
        self._run_tlp(view, TLP_PROFILES[i])

    def action_conservation(self) -> None:
        view = self.query_one("#conservation-view", ConservationView)
        new_state = view.toggle()
        if new_state is None:
            return
        self.run_worker(
            lambda: self._write_conservation(new_state),
            exclusive=False,
            thread=True,
        )

    # ── Threaded write helpers ────────────────────────────────────────────────

    def _run_tlp(self, view: TlpView, profile: str | None) -> None:
        if not profile:
            view.show_feedback(False, "TLP is not installed")
            return
        def _worker() -> None:
            success, msg = set_tlp_profile(profile)
            self.call_from_thread(view.show_feedback, success, msg)
            if success:
                self.call_from_thread(self._apply_tlp, get_tlp_status())
        self.run_worker(_worker, exclusive=False, thread=True)

    def _write_conservation(self, new_state: bool) -> None:
        success, msg = set_conservation_mode(new_state)
        view = self.query_one("#conservation-view", ConservationView)
        self.call_from_thread(view.show_feedback, success, msg)
        if success:
            self.call_from_thread(view.apply_toggle, new_state)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sysinfo_text(self) -> str:
        parts = [f"Vendor: {self._hw.vendor}"]
        if self._hw.is_vm:
            parts.append("(VM)")
        parts.append(f"Batteries: {len(self._hw.battery_paths)}")
        return "  │  ".join(parts)
