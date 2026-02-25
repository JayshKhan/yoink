from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Select, SelectionList, Static

from yoink.core.models import PlaylistInfo, VideoInfo


class PlaylistPanel(Widget):
    """Displays playlist info with selectable videos, quality picker, and download button."""

    class DownloadVideosRequested(Message):
        def __init__(self, videos: list[VideoInfo], quality: str) -> None:
            self.videos = videos
            self.quality = quality
            super().__init__()

    DEFAULT_CSS = """
    PlaylistPanel {
        height: 1fr;
        padding: 1 2;
        layout: vertical;
    }
    PlaylistPanel #playlist-meta {
        height: auto;
        margin-bottom: 1;
    }
    PlaylistPanel #playlist-controls {
        height: 3;
        margin-bottom: 1;
        align-vertical: middle;
    }
    PlaylistPanel #playlist-controls Button {
        margin-right: 1;
    }
    PlaylistPanel #playlist-controls Label {
        padding-top: 1;
        margin-right: 1;
    }
    PlaylistPanel #playlist-quality {
        width: 30;
    }
    PlaylistPanel SelectionList {
        height: 1fr;
        border: tall $surface-lighten-2;
    }
    PlaylistPanel #playlist-download-btn {
        width: 100%;
        margin-top: 1;
    }
    """

    QUALITY_OPTIONS = [
        ("Best (1080p+)", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
        ("720p", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"),
        ("480p", "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"),
        ("Audio only (m4a)", "bestaudio[ext=m4a]/bestaudio"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._playlist: PlaylistInfo | None = None

    def compose(self) -> ComposeResult:
        yield Static("", id="playlist-meta")
        with Horizontal(id="playlist-controls"):
            yield Button("Select All", id="select-all-btn", variant="default")
            yield Button("Select None", id="select-none-btn", variant="default")
            yield Label("Quality:")
            yield Select(
                [(label, val) for label, val in self.QUALITY_OPTIONS],
                id="playlist-quality",
                value=self.QUALITY_OPTIONS[0][1],
            )
        yield SelectionList[str](id="video-selection")
        yield Button(
            "\u2b07 Download Selected", variant="success", id="playlist-download-btn", disabled=True
        )

    def set_playlist(self, playlist: PlaylistInfo) -> None:
        self._playlist = playlist

        meta = self.query_one("#playlist-meta", Static)
        meta.update(
            f"[bold]{playlist.title}[/bold]\n"
            f"[dim]{playlist.video_count} videos[/dim]"
        )

        sel = self.query_one("#video-selection", SelectionList)
        sel.clear_options()
        for i, video in enumerate(playlist.videos):
            duration = ""
            if video.duration:
                m, s = divmod(video.duration, 60)
                duration = f" [{m}:{s:02d}]"
            sel.add_option(
                (f"{i + 1}. {video.title}{duration}", video.video_id)
            )

        btn = self.query_one("#playlist-download-btn", Button)
        btn.disabled = playlist.video_count == 0

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "select-all-btn":
            sel = self.query_one("#video-selection", SelectionList)
            sel.select_all()
        elif event.button.id == "select-none-btn":
            sel = self.query_one("#video-selection", SelectionList)
            sel.deselect_all()
        elif event.button.id == "playlist-download-btn":
            self._request_download()

    def _request_download(self) -> None:
        if self._playlist is None:
            return
        sel = self.query_one("#video-selection", SelectionList)
        selected_ids = set(sel.selected)
        videos = [v for v in self._playlist.videos if v.video_id in selected_ids]
        if not videos:
            self.notify("No videos selected", severity="warning")
            return

        quality_select = self.query_one("#playlist-quality", Select)
        quality = str(quality_select.value) if quality_select.value != Select.BLANK else self.QUALITY_OPTIONS[0][1]

        self.post_message(self.DownloadVideosRequested(videos, quality))
