"""Linux Power Manager — CLI entrypoint."""

from __future__ import annotations

from power_manager.ui.app import PowerManagerApp


def main() -> None:
    """Run the TUI application."""
    app = PowerManagerApp()
    app.run()
