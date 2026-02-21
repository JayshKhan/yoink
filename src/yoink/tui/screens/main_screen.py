from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, ContentSwitcher, Static
from textual import work

from yoink.core.manager import DownloadManager
from yoink.core.models import DownloadRequest, FormatOption, PlaylistInfo, VideoInfo

from ..logo import LOGO
from ..widgets.download_item import DownloadItem
from ..widgets.download_queue import DownloadQueue
from ..widgets.playlist_panel import PlaylistPanel
from ..widgets.url_bar import URLBar
from ..widgets.video_info_panel import VideoInfoPanel


class MainScreen(Screen):
    """Primary screen composing URL bar, content area, and download queue."""

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    #content-area {
        height: 1fr;
    }
    #welcome-view {
        align: center middle;
        height: 100%;
    }
    .welcome-text {
        color: $text-muted;
        text-align: center;
    }
    #loading-view {
        align: center middle;
        height: 100%;
    }
    #video-view {
        height: 100%;
    }
    #playlist-view {
        height: 100%;
    }
    #error-view {
        align: center middle;
        height: 100%;
    }
    .error-text {
        color: $error;
        text-align: center;
        width: 100%;
    }
    """

    BINDINGS = [
        ("slash", "focus_url", "Focus URL"),
        ("d", "download", "Download"),
        ("r", "retry_last", "Retry Last"),
    ]

    def __init__(self, manager: DownloadManager) -> None:
        super().__init__()
        self.manager = manager
        self._current_video: VideoInfo | None = None
        self._current_playlist: PlaylistInfo | None = None

    def compose(self) -> ComposeResult:
        yield URLBar()
        with ContentSwitcher(id="content-area", initial="welcome-view"):
            with Container(id="welcome-view"):
                yield Static(
                    LOGO + "\nPaste a YouTube URL above and press Enter.",
                    classes="welcome-text",
                )
            with Container(id="loading-view"):
                yield Static("Fetching video info...", classes="welcome-text")
            with Container(id="video-view"):
                yield VideoInfoPanel()
            with Container(id="playlist-view"):
                yield PlaylistPanel()
            with Container(id="error-view"):
                yield Static("", classes="error-text", id="error-text")
        yield DownloadQueue(self.manager)

    def on_url_bar_submitted(self, event: URLBar.Submitted) -> None:
        self._fetch_url(event.url)

    def on_url_bar_output_dir_changed(self, event: URLBar.OutputDirChanged) -> None:
        self.app.output_dir = event.path

    @property
    def _switcher(self) -> ContentSwitcher:
        return self.query_one("#content-area", ContentSwitcher)

    def _fetch_url(self, url: str) -> None:
        self._switcher.current = "loading-view"
        self.notify("Fetching info...")
        self._do_fetch(url)

    @work(exclusive=True, thread=False)
    async def _do_fetch(self, url: str) -> None:
        try:
            is_playlist = await self.manager.is_playlist(url)
            if is_playlist:
                playlist = await self.manager.get_playlist_info(url)
                self._current_playlist = playlist
                self._show_playlist(playlist)
            else:
                video = await self.manager.get_video_info(url)
                self._current_video = video
                self._show_video(video)
        except Exception as e:
            self._show_error(str(e))

    def _show_video(self, info: VideoInfo) -> None:
        panel = self.query_one(VideoInfoPanel)
        panel.set_video(info)
        self._switcher.current = "video-view"

    def _show_playlist(self, playlist: PlaylistInfo) -> None:
        panel = self.query_one(PlaylistPanel)
        panel.set_playlist(playlist)
        self._switcher.current = "playlist-view"

    def _show_error(self, message: str) -> None:
        error_text = self.query_one("#error-text", Static)
        error_text.update(f"[bold red]Error:[/bold red] {message}")
        self._switcher.current = "error-view"

    # -- Keyboard shortcuts --

    def action_focus_url(self) -> None:
        from textual.widgets import Input
        url_bar = self.query_one(URLBar)
        url_input = url_bar.query_one("#url-input", Input)
        url_input.focus()

    def action_download(self) -> None:
        current = self._switcher.current
        if current == "video-view":
            panel = self.query_one(VideoInfoPanel)
            panel.action_download()
        elif current == "playlist-view":
            panel = self.query_one(PlaylistPanel)
            panel.action_download()

    def action_retry_last(self) -> None:
        queue = self.query_one(DownloadQueue)
        # Find the last failed/cancelled item and retry it
        for download_id in reversed(list(queue._items)):
            item = queue._items[download_id]
            btn = item.query_one(".dl-cancel", Button)
            if str(btn.label) == "Retry":
                item.post_message(DownloadItem.RetryRequested(download_id))
                break

    # -- Single video download --

    def on_video_info_panel_download_requested(
        self, event: VideoInfoPanel.DownloadRequested
    ) -> None:
        self._start_video_download(
            event.video_info,
            event.format_option,
            download_subtitles=event.download_subtitles,
            convert_to_mp3=event.convert_to_mp3,
            output_template=event.output_template,
        )

    def _start_video_download(
        self,
        video: VideoInfo,
        fmt: FormatOption,
        download_subtitles: bool = False,
        convert_to_mp3: bool = False,
        output_template: str = "%(title)s.%(ext)s",
    ) -> None:
        if fmt.has_video and not fmt.has_audio:
            format_string = f"{fmt.format_id}+bestaudio"
        else:
            format_string = fmt.format_id

        request = DownloadRequest(
            url=video.url,
            format_string=format_string,
            output_dir=self.app.output_dir,
            output_template=output_template,
            download_subtitles=download_subtitles,
            convert_to_mp3=convert_to_mp3,
        )
        queue = self.query_one(DownloadQueue)
        result = queue.add_download(request, title=video.title)
        if result is not None:
            self.notify(f"Started: {video.title}")

    # -- Playlist download --

    def on_playlist_panel_download_videos_requested(
        self, event: PlaylistPanel.DownloadVideosRequested
    ) -> None:
        queue = self.query_one(DownloadQueue)
        count = 0
        for video in event.videos:
            request = DownloadRequest(
                url=f"https://www.youtube.com/watch?v={video.video_id}",
                format_string=event.quality,
                output_dir=self.app.output_dir,
                output_template=event.output_template,
                download_subtitles=event.download_subtitles,
            )
            result = queue.add_download(request, title=video.title)
            if result is not None:
                count += 1
        if count:
            self.notify(f"Queued {count} downloads")
