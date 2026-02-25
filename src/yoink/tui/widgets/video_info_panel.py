from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, Select, Static

from yoink.core.models import FormatOption, VideoInfo


class VideoInfoPanel(Widget):
    """Displays video metadata, quality picker, and download button."""

    class DownloadRequested(Message):
        def __init__(self, video_info: VideoInfo, format_option: FormatOption) -> None:
            self.video_info = video_info
            self.format_option = format_option
            super().__init__()

    DEFAULT_CSS = """
    VideoInfoPanel {
        height: 1fr;
        padding: 1 2;
        layout: vertical;
    }
    VideoInfoPanel #video-meta {
        height: auto;
        margin-bottom: 1;
    }
    VideoInfoPanel #quality-row {
        height: 3;
        margin: 1 0;
        align-vertical: middle;
    }
    VideoInfoPanel #quality-row Label {
        width: auto;
        margin-right: 1;
        padding-top: 1;
    }
    VideoInfoPanel #quality-select {
        width: 1fr;
    }
    VideoInfoPanel #download-video-btn {
        width: 100%;
        margin-top: 1;
    }
    VideoInfoPanel #format-details {
        height: auto;
        max-height: 12;
        margin-top: 1;
        border: tall $surface-lighten-2;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._video_info: VideoInfo | None = None
        self._formats: list[FormatOption] = []

    def compose(self) -> ComposeResult:
        yield Static("", id="video-meta")
        with Horizontal(id="quality-row"):
            yield Label("Quality:")
            yield Select([], id="quality-select", prompt="Select quality")
        yield Button(
            "\u2b07 Download", variant="success", id="download-video-btn", disabled=True
        )
        yield DataTable(id="format-details", cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#format-details", DataTable)
        table.add_columns("Format", "Resolution", "Ext", "Size", "Codecs")

    def set_video(self, info: VideoInfo) -> None:
        self._video_info = info
        self._formats = info.formats

        meta = self.query_one("#video-meta", Static)
        parts = [f"[bold]{info.title}[/bold]"]
        if info.uploader:
            parts.append(f"[dim]{info.uploader}[/dim]")
        details = []
        if info.duration is not None:
            details.append(info.duration_display)
        if info.view_count is not None:
            details.append(f"{info.view_count:,} views")
        if details:
            parts.append(" | ".join(details))
        meta.update("\n".join(parts))

        # Populate quality dropdown
        options: list[tuple[str, int]] = []
        for i, fmt in enumerate(self._formats):
            size = FormatOption._human_size(fmt.filesize) if fmt.filesize else ""
            label_parts = []
            if fmt.resolution:
                label_parts.append(fmt.resolution)
            elif fmt.has_audio and not fmt.has_video:
                label_parts.append("Audio only")
            if fmt.format_note:
                label_parts.append(fmt.format_note)
            if fmt.ext:
                label_parts.append(fmt.ext.upper())
            if size:
                label_parts.append(size)
            if fmt.has_video and fmt.has_audio:
                label_parts.append("(A+V)")
            elif fmt.has_video:
                label_parts.append("(V)")
            elif fmt.has_audio:
                label_parts.append("(A)")
            options.append((" | ".join(label_parts) or fmt.format_id, i))

        select = self.query_one("#quality-select", Select)
        select.set_options(options)
        if options:
            select.value = 0  # select first (highest quality)

        # Populate details table
        table = self.query_one("#format-details", DataTable)
        table.clear()
        for fmt in self._formats:
            codecs = []
            if fmt.has_video:
                codecs.append(fmt.vcodec.split(".")[0])
            if fmt.has_audio:
                codecs.append(fmt.acodec.split(".")[0])
            size = FormatOption._human_size(fmt.filesize) if fmt.filesize else "?"
            table.add_row(
                fmt.format_note or fmt.format_id,
                fmt.resolution or ("Audio" if fmt.has_audio else "-"),
                fmt.ext,
                size,
                "+".join(codecs),
                key=fmt.format_id,
            )

        btn = self.query_one("#download-video-btn", Button)
        btn.disabled = len(self._formats) == 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "download-video-btn":
            return
        if self._video_info is None:
            return
        select = self.query_one("#quality-select", Select)
        if select.value is not None and select.value != Select.BLANK:
            idx = int(select.value)
            if idx < len(self._formats):
                fmt = self._formats[idx]
                self.post_message(self.DownloadRequested(self._video_info, fmt))
