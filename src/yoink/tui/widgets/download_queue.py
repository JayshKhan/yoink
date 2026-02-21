from __future__ import annotations

import re
import uuid

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widget import Widget
from textual.widgets import Button, Input, Label

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
    DownloadQueue #speed-limit-input {
        width: 10;
        margin-left: 1;
        margin-right: 1;
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
        self._requests: dict[str, DownloadRequest] = {}
        self._speed_limit: int | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="queue-header"):
            yield Label("Downloads", classes="queue-title")
            yield Input(placeholder="Speed (e.g. 5M)", id="speed-limit-input")
            yield Label(self._slots_text(), id="slots-label", classes="slots-label")
            yield Button("-", id="slots-down", variant="default")
            yield Button("+", id="slots-up", variant="default")
        yield VerticalScroll(id="download-list")

    def _slots_text(self) -> str:
        active = self.manager.active_count
        limit = self.manager.max_concurrent
        queued = self.manager.queued_count
        text = f"[{active}/{limit}]"
        if queued > 0:
            text += f" {queued} waiting"
        return text

    def _update_slots_label(self) -> None:
        label = self.query_one("#slots-label", Label)
        label.update(self._slots_text())

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "speed-limit-input":
            self._speed_limit = self._parse_speed(event.value.strip())

    @staticmethod
    def _parse_speed(value: str) -> int | None:
        if not value:
            return None
        match = re.match(r"^(\d+(?:\.\d+)?)\s*([kmg])?b?/?s?$", value, re.I)
        if not match:
            return None
        num = float(match.group(1))
        unit = (match.group(2) or "").upper()
        multipliers = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}
        return int(num * multipliers.get(unit, 1))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "slots-up":
            self.manager.max_concurrent += 1
            self._update_slots_label()
        elif event.button.id == "slots-down":
            self.manager.max_concurrent -= 1
            self._update_slots_label()

    def add_download(self, request: DownloadRequest, title: str = "") -> str | None:
        if self._speed_limit:
            request = request.model_copy(update={"speed_limit": self._speed_limit})

        def _on_progress(progress: DownloadProgress) -> None:
            self.app.call_from_thread(self._on_progress_update, progress)

        result = self.manager.start_download(request, callback=_on_progress)
        if result is None:
            self.notify("Already downloading this URL", severity="warning")
            return None

        item = DownloadItem(download_id=request.download_id, title=title)
        self._items[request.download_id] = item
        self._requests[request.download_id] = request
        self.query_one("#download-list", VerticalScroll).mount(item)
        self._update_slots_label()
        return request.download_id

    def _on_progress_update(self, progress: DownloadProgress) -> None:
        item = self._items.get(progress.download_id)
        if item:
            item.update_progress(progress)
        self._update_slots_label()

    def on_download_item_cancel_requested(
        self, event: DownloadItem.CancelRequested
    ) -> None:
        self.manager.cancel_download(event.download_id)

    def on_download_item_retry_requested(
        self, event: DownloadItem.RetryRequested
    ) -> None:
        old_request = self._requests.get(event.download_id)
        if old_request is None:
            return

        new_id = uuid.uuid4().hex[:12]
        new_request = old_request.model_copy(update={"download_id": new_id})

        # Reuse the existing item widget
        item = self._items.pop(event.download_id)
        item.download_id = new_id
        item.reset_for_retry()
        self._items[new_id] = item
        self._requests[new_id] = new_request

        def _on_progress(progress: DownloadProgress) -> None:
            self.app.call_from_thread(self._on_progress_update, progress)

        self.manager.start_download(new_request, callback=_on_progress, force=True)
        self._update_slots_label()
