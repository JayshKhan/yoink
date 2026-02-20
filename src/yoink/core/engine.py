from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path

import yt_dlp

from .models import DownloadProgress, DownloadRequest, DownloadStatus


class DownloadCancelled(Exception):
    pass


class DownloadEngine:
    """Executes a single download with progress reporting. Runs synchronously in a thread."""

    def __init__(
        self,
        request: DownloadRequest,
        callback: Callable[[DownloadProgress], None] | None = None,
    ):
        self.request = request
        self.callback = callback
        self._cancel_event = threading.Event()
        self._last_callback_time: float = 0
        self._progress = DownloadProgress(
            download_id=request.download_id,
            status=DownloadStatus.QUEUED,
        )

    def run(self) -> DownloadProgress:
        """Execute the download. Call from a thread pool."""
        output_dir = Path(self.request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(output_dir / self.request.output_template)

        ydl_opts = {
            "format": self.request.format_string,
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._progress_hook],
            "postprocessor_hooks": [self._postprocessor_hook],
            "noprogress": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.request.url, download=False)
                if info:
                    self._progress.title = info.get("title", "Unknown")
                self._update_status(DownloadStatus.DOWNLOADING)
                ydl.download([self.request.url])

            self._update_status(DownloadStatus.FINISHED)
            self._progress.percent = 100.0
            self._emit_progress(force=True)
        except DownloadCancelled:
            self._update_status(DownloadStatus.CANCELLED)
            self._emit_progress(force=True)
        except Exception as e:
            self._progress.error = str(e)
            self._update_status(DownloadStatus.ERROR)
            self._emit_progress(force=True)

        return self._progress

    def cancel(self) -> None:
        self._cancel_event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def _progress_hook(self, d: dict) -> None:
        if self._cancel_event.is_set():
            raise DownloadCancelled()

        status = d.get("status", "")
        if status == "downloading":
            self._progress.status = DownloadStatus.DOWNLOADING
            self._progress.downloaded_bytes = d.get("downloaded_bytes", 0)
            self._progress.total_bytes = (
                d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            )
            self._progress.speed = d.get("speed") or 0.0
            self._progress.eta = d.get("eta")
            if self._progress.total_bytes > 0:
                self._progress.percent = (
                    self._progress.downloaded_bytes / self._progress.total_bytes * 100
                )
            self._emit_progress()
        elif status == "finished":
            self._progress.percent = 100.0
            self._progress.status = DownloadStatus.MERGING
            self._emit_progress(force=True)

    def _postprocessor_hook(self, d: dict) -> None:
        if self._cancel_event.is_set():
            raise DownloadCancelled()
        status = d.get("status", "")
        if status == "started":
            self._progress.status = DownloadStatus.MERGING
            self._emit_progress(force=True)

    def _update_status(self, status: DownloadStatus) -> None:
        self._progress.status = status

    def _emit_progress(self, force: bool = False) -> None:
        if self.callback is None:
            return
        now = time.monotonic()
        if not force and (now - self._last_callback_time) < 0.1:
            return
        self._last_callback_time = now
        self.callback(self._progress.model_copy())
