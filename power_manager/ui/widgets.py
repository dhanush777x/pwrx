"""
Reusable Textual widgets.
Zero hardcoded colours — all styling via var(--pm-*) from app.py Screen block.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Label, Static


class SectionHeader(Static):
    """Panel title bar — styled via app.py SectionHeader rule."""
    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(f" {title}", **kwargs)


class StatusRow(Static):
    """Key / value display row."""
    DEFAULT_CSS = """
    StatusRow {
        height: 1;
        padding: 0 2;
        layout: horizontal;
        background: transparent;
    }
    StatusRow .key   { width: 22; }
    StatusRow .value { }
    """

    def __init__(self, key: str, value: str = "—", **kwargs) -> None:
        super().__init__(**kwargs)
        self._key   = key
        self._value = value

    def compose(self) -> ComposeResult:
        yield Label(f"{self._key:<22}", classes="key")
        yield Label(self._value,        classes="value")

    def update_value(self, value: str) -> None:
        self.query_one(".value", Label).update(value)


class ErrorBanner(Static):
    """Error banner — styled via app.py ErrorBanner rule."""
    message: reactive[str] = reactive("")

    def show(self, message: str) -> None:
        self.message = message
        self.add_class("visible")

    def hide(self) -> None:
        self.remove_class("visible")

    def render(self) -> str:
        return f" ⚠  {self.message}"


class InfoBanner(Static):
    """Success banner — auto-hides after 3 s."""
    message: reactive[str] = reactive("")

    def show(self, message: str) -> None:
        self.message = message
        self.add_class("visible")
        self.set_timer(3.0, self.hide)

    def hide(self) -> None:
        self.remove_class("visible")

    def render(self) -> str:
        return f" ✓  {self.message}"
