from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, ProgressBar

from yoink.core.models import DownloadProgress, DownloadStatus


class DownloadItem(Widget):
    """A single download row with progress bar, speed, ETA, and cancel button."""

    class CancelRequested(Message):
        def __init__(self, download_id: str) -> None:
            self.download_id = download_id
            super().__init__()

    DEFAULT_CSS = """
    DownloadItem {
        height: 3;
        padding: 0 1;
    }
    DownloadItem Horizontal {
        height: 3;
        align-vertical: middle;
    }
    DownloadItem .dl-title {
        width: 30;
        overflow: hidden;
    }
    DownloadItem ProgressBar {
        width: 1fr;
        margin: 0 1;
    }
    DownloadItem .dl-status {
        width: 20;
        text-align: right;
    }
    DownloadItem .dl-cancel {
        min-width: 8;
        margin-left: 1;
    }
    """

    def __init__(self, download_id: str, title: str = "") -> None:
        super().__init__()
        self.download_id = download_id
        self._title = title or "Loading..."

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(self._truncate(self._title, 28), classes="dl-title")
            yield ProgressBar(total=100, show_percentage=True, show_eta=False)
            yield Label("Queued", classes="dl-status")
            yield Button("X", variant="error", classes="dl-cancel")

    def update_progress(self, progress: DownloadProgress) -> None:
        title_label = self.query_one(".dl-title", Label)
        bar = self.query_one(ProgressBar)
        status_label = self.query_one(".dl-status", Label)
        cancel_btn = self.query_one(".dl-cancel", Button)

        if progress.title:
            title_label.update(self._truncate(progress.title, 28))

        bar.progress = progress.percent

        if progress.status == DownloadStatus.DOWNLOADING:
            parts = []
            if progress.speed > 0:
                parts.append(progress.speed_display)
            if progress.eta is not None and progress.eta >= 0:
                parts.append(progress.eta_display)
            status_label.update(" | ".join(parts) if parts else "Downloading...")
        elif progress.status == DownloadStatus.MERGING:
            status_label.update("Merging...")
        elif progress.status == DownloadStatus.FINISHED:
            status_label.update("Done!")
            cancel_btn.disabled = True
        elif progress.status == DownloadStatus.ERROR:
            status_label.update("Error")
            cancel_btn.disabled = True
        elif progress.status == DownloadStatus.CANCELLED:
            status_label.update("Cancelled")
            cancel_btn.disabled = True
        else:
            status_label.update("Queued")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if "dl-cancel" in event.button.classes:
            self.post_message(self.CancelRequested(self.download_id))

    @staticmethod
    def _truncate(text: str, length: int) -> str:
        if len(text) <= length:
            return text
        return text[: length - 1] + "\u2026"
