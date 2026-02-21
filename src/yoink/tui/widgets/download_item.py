from __future__ import annotations

import platform
import subprocess
from pathlib import Path

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

    class RetryRequested(Message):
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
        width: 30;
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
        self._output_path: str | None = None

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

        if progress.output_path:
            self._output_path = progress.output_path

        bar.progress = progress.percent

        if progress.status == DownloadStatus.DOWNLOADING:
            parts = []
            if progress.size_display:
                parts.append(progress.size_display)
            if progress.speed > 0:
                parts.append(progress.speed_display)
            if progress.eta is not None and progress.eta >= 0:
                parts.append(progress.eta_display)
            status_label.update(" | ".join(parts) if parts else "Downloading...")
        elif progress.status == DownloadStatus.MERGING:
            status_label.update("Merging...")
        elif progress.status == DownloadStatus.FINISHED:
            status_label.update("Done!")
            cancel_btn.label = "Open"
            cancel_btn.variant = "success"
            cancel_btn.disabled = False
        elif progress.status == DownloadStatus.ERROR:
            error_msg = progress.error or "Error"
            status_label.update(self._truncate(error_msg, 26))
            cancel_btn.label = "Retry"
            cancel_btn.variant = "warning"
            cancel_btn.disabled = False
        elif progress.status == DownloadStatus.CANCELLED:
            status_label.update("Cancelled")
            cancel_btn.label = "Retry"
            cancel_btn.variant = "warning"
            cancel_btn.disabled = False
        else:
            status_label.update("Queued")

    def reset_for_retry(self) -> None:
        bar = self.query_one(ProgressBar)
        status_label = self.query_one(".dl-status", Label)
        cancel_btn = self.query_one(".dl-cancel", Button)
        bar.progress = 0
        status_label.update("Queued")
        cancel_btn.label = "X"
        cancel_btn.variant = "error"
        cancel_btn.disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if "dl-cancel" not in event.button.classes:
            return
        label = str(event.button.label)
        if label == "Retry":
            self.post_message(self.RetryRequested(self.download_id))
        elif label == "Open":
            self._open_folder()
        else:
            self.post_message(self.CancelRequested(self.download_id))

    def _open_folder(self) -> None:
        if not self._output_path:
            return
        folder = str(Path(self._output_path).parent)
        system = platform.system()
        try:
            if system == "Darwin":
                subprocess.Popen(["open", folder])
            elif system == "Linux":
                subprocess.Popen(["xdg-open", folder])
            else:
                subprocess.Popen(["explorer", folder])
        except OSError:
            pass

    @staticmethod
    def _truncate(text: str, length: int) -> str:
        if len(text) <= length:
            return text
        return text[: length - 1] + "\u2026"
