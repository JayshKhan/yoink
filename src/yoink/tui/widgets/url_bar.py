from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label


class URLBar(Widget):
    """URL input bar with a Fetch button and output directory picker."""

    class Submitted(Message):
        def __init__(self, url: str) -> None:
            self.url = url
            super().__init__()

    class OutputDirChanged(Message):
        def __init__(self, path: str) -> None:
            self.path = path
            super().__init__()

    DEFAULT_CSS = """
    URLBar {
        dock: top;
        height: auto;
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
    URLBar #dir-row {
        height: 3;
    }
    URLBar #dir-row Label {
        width: auto;
        padding-top: 1;
        margin-right: 1;
        color: $text-muted;
    }
    URLBar #dir-input {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            with Horizontal(id="url-row"):
                yield Input(placeholder="Paste a YouTube URL...", id="url-input")
                yield Button("Fetch", variant="primary", id="fetch-btn")
            with Horizontal(id="dir-row"):
                yield Label("Save to:")
                yield Input(
                    str(Path.home() / "Downloads"),
                    placeholder="Output directory...",
                    id="dir-input",
                )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "url-input":
            url = event.value.strip()
            if url:
                self.post_message(self.Submitted(url))

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "dir-input":
            self.post_message(self.OutputDirChanged(event.value.strip()))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fetch-btn":
            inp = self.query_one("#url-input", Input)
            url = inp.value.strip()
            if url:
                self.post_message(self.Submitted(url))
