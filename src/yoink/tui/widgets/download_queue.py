from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Label

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
    DownloadQueue #queue-header {
        height: 3;
        padding: 0 1;
        background: $surface;
        align-vertical: middle;
    }
    DownloadQueue #queue-header .queue-title {
        width: 1fr;
        text-style: bold;
        color: $text;
        padding-top: 1;
    }
    DownloadQueue #queue-header .slots-label {
        width: auto;
        padding-top: 1;
        margin-right: 1;
        color: $text-muted;
    }
    DownloadQueue #queue-header Button {
        min-width: 3;
        max-width: 3;
        margin: 0;
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
        with Horizontal(id="queue-header"):
            yield Label("Downloads", classes="queue-title")
            yield Label(
                f"Slots: {self.manager.max_concurrent}",
                id="slots-label",
                classes="slots-label",
            )
            yield Button("-", id="slots-down", variant="default")
            yield Button("+", id="slots-up", variant="default")
        yield VerticalScroll(id="download-list")

    def _update_slots_label(self) -> None:
        label = self.query_one("#slots-label", Label)
        label.update(f"Slots: {self.manager.max_concurrent}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "slots-up":
            self.manager.max_concurrent += 1
            self._update_slots_label()
            self.notify(f"Max concurrent: {self.manager.max_concurrent}")
        elif event.button.id == "slots-down":
            self.manager.max_concurrent -= 1
            self._update_slots_label()
            self.notify(f"Max concurrent: {self.manager.max_concurrent}")

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
