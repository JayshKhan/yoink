from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widget import Widget
from textual.widgets import Label

from yoink.core.manager import DownloadManager
from yoink.core.models import DownloadProgress, DownloadRequest

from .download_item import DownloadItem


class DownloadQueue(Widget):
    """Container for active and completed downloads."""

    DEFAULT_CSS = """
    DownloadQueue {
        dock: bottom;
        height: auto;
        max-height: 50%;
        border-top: solid $accent;
    }
    DownloadQueue .queue-header {
        padding: 0 1;
        text-style: bold;
        color: $text;
        background: $surface;
    }
    DownloadQueue VerticalScroll {
        height: auto;
        max-height: 100%;
    }
    """

    def __init__(self, manager: DownloadManager) -> None:
        super().__init__()
        self.manager = manager
        self._items: dict[str, DownloadItem] = {}

    def compose(self) -> ComposeResult:
        yield Label("Downloads", classes="queue-header")
        yield VerticalScroll(id="download-list")

    def add_download(self, request: DownloadRequest, title: str = "") -> str:
        item = DownloadItem(download_id=request.download_id, title=title)
        self._items[request.download_id] = item
        self.query_one("#download-list", VerticalScroll).mount(item)

        def _on_progress(progress: DownloadProgress) -> None:
            self.app.call_from_thread(self._update_item, progress)

        self.manager.start_download(request, callback=_on_progress)
        return request.download_id

    def _update_item(self, progress: DownloadProgress) -> None:
        item = self._items.get(progress.download_id)
        if item:
            item.update_progress(progress)

    def on_download_item_cancel_requested(
        self, event: DownloadItem.CancelRequested
    ) -> None:
        self.manager.cancel_download(event.download_id)
