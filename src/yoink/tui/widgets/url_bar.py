from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input


class URLBar(Widget):
    """URL input bar with a Fetch button."""

    class Submitted(Message):
        def __init__(self, url: str) -> None:
            self.url = url
            super().__init__()

    DEFAULT_CSS = """
    URLBar {
        dock: top;
        height: 3;
        padding: 0 1;
    }
    URLBar Horizontal {
        height: 3;
    }
    URLBar Input {
        width: 1fr;
    }
    URLBar Button {
        min-width: 12;
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(placeholder="Paste a YouTube URL...", id="url-input")
            yield Button("Fetch", variant="primary", id="fetch-btn")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        url = event.value.strip()
        if url:
            self.post_message(self.Submitted(url))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fetch-btn":
            inp = self.query_one("#url-input", Input)
            url = inp.value.strip()
            if url:
                self.post_message(self.Submitted(url))
