from __future__ import annotations

import argparse
import shutil

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from yoink.core.manager import DownloadManager

from .screens.main_screen import MainScreen


class YoinkApp(App):
    """Yoink - grab videos off YouTube."""

    TITLE = "yoink"
    SUB_TITLE = "grab videos, fast"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, max_concurrent: int = 3) -> None:
        super().__init__()
        self.manager = DownloadManager(max_concurrent=max_concurrent)

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
    parser = argparse.ArgumentParser(
        prog="yoink",
        description="Grab videos off YouTube.",
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=3,
        metavar="N",
        help="max simultaneous downloads (default: 3, range: 1-10)",
    )
    args = parser.parse_args()
    jobs = max(1, min(args.jobs, 10))

    app = YoinkApp(max_concurrent=jobs)
    app.run()


if __name__ == "__main__":
    main()
