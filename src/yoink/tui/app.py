from __future__ import annotations

import shutil

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from yoink.core.manager import DownloadManager

from .screens.main_screen import MainScreen

LOGO = """\
[bold red]╭──╮[/]  [bold white]yoink[/]
[bold red]│▶ │[/]  [dim]grab videos, fast[/dim]
[bold red]╰──╯[/]\
"""


class YoinkApp(App):
    """Yoink - grab videos off YouTube."""

    TITLE = "yoink"
    SUB_TITLE = "grab videos, fast"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.manager = DownloadManager(max_concurrent=3)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.manager))
        if not shutil.which("ffmpeg"):
            self.notify(
                "ffmpeg not found. Some formats may not merge correctly.",
                severity="warning",
                timeout=5,
            )

    def on_unmount(self) -> None:
        self.manager.shutdown()


def main() -> None:
    app = YoinkApp()
    app.run()


if __name__ == "__main__":
    main()
