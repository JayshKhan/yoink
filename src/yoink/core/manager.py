from __future__ import annotations

import asyncio
import queue
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from .engine import DownloadEngine
from .extractor import MetadataExtractor
from .models import (
    DownloadProgress,
    DownloadRequest,
    DownloadStatus,
    FormatOption,
    PlaylistInfo,
    VideoInfo,
)


class DownloadManager:
    """Orchestrates concurrent downloads and metadata extraction.

    Uses a FIFO queue with a dispatcher thread to ensure downloads
    start in the order they were submitted. Active count is tracked
    explicitly so the concurrency limit can be changed at runtime
    without affecting in-progress downloads.
    """

    def __init__(self, max_concurrent: int = 3):
        self._max_concurrent = max_concurrent
        self._active_count = 0
        self._lock = threading.Lock()
        self._slot_available = threading.Condition(self._lock)
        self._queue: queue.Queue[DownloadEngine] = queue.Queue()
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._extractor = MetadataExtractor()
        self._engines: dict[str, DownloadEngine] = {}
        self._progress: dict[str, DownloadProgress] = {}
        self._url_to_id: dict[str, str] = {}
        self._shutdown_event = threading.Event()

        self._dispatcher = threading.Thread(
            target=self._dispatch_loop, daemon=True
        )
        self._dispatcher.start()

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        value = max(1, min(value, 10))
        with self._slot_available:
            self._max_concurrent = value
            # Wake dispatcher — if limit went up, it can start more
            self._slot_available.notify()

    @property
    def active_count(self) -> int:
        with self._lock:
            return self._active_count

    @property
    def queued_count(self) -> int:
        return self._queue.qsize()

    # -- Dispatcher: ensures FIFO ordering --

    def _dispatch_loop(self) -> None:
        while not self._shutdown_event.is_set():
            try:
                engine = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            # Wait until there's room to start this download
            with self._slot_available:
                while (
                    self._active_count >= self._max_concurrent
                    and not self._shutdown_event.is_set()
                ):
                    self._slot_available.wait(timeout=0.5)

                if engine.is_cancelled:
                    continue

                self._active_count += 1

            self._executor.submit(self._run_and_release, engine)

    def _run_and_release(self, engine: DownloadEngine) -> None:
        try:
            engine.run()
        finally:
            with self._slot_available:
                self._active_count -= 1
                self._slot_available.notify()

    # -- Async metadata wrappers (run sync yt-dlp in thread pool) --

    async def get_video_info(self, url: str) -> VideoInfo:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._extractor.extract_video_info, url
        )

    async def get_playlist_info(self, url: str) -> PlaylistInfo:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._extractor.extract_playlist_info, url
        )

    async def get_formats(self, url: str) -> list[FormatOption]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._extractor.extract_formats, url
        )

    async def is_playlist(self, url: str) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._extractor.is_playlist, url
        )

    # -- Download management --

    def start_download(
        self,
        request: DownloadRequest,
        callback: Callable[[DownloadProgress], None] | None = None,
        force: bool = False,
    ) -> str | None:
        download_id = request.download_id

        if not force:
            existing_id = self._url_to_id.get(request.url)
            if existing_id:
                existing_progress = self._progress.get(existing_id)
                if existing_progress and existing_progress.status in (
                    DownloadStatus.QUEUED,
                    DownloadStatus.DOWNLOADING,
                    DownloadStatus.MERGING,
                ):
                    return None

        self._url_to_id[request.url] = download_id

        def _on_progress(progress: DownloadProgress) -> None:
            self._progress[download_id] = progress
            if progress.status in (
                DownloadStatus.FINISHED,
                DownloadStatus.ERROR,
                DownloadStatus.CANCELLED,
            ):
                self._url_to_id.pop(request.url, None)
            if callback:
                callback(progress)

        engine = DownloadEngine(request, callback=_on_progress)
        self._engines[download_id] = engine
        self._progress[download_id] = DownloadProgress(download_id=download_id)
        self._queue.put(engine)
        return download_id

    def get_progress(self, download_id: str) -> DownloadProgress | None:
        return self._progress.get(download_id)

    def get_all_progress(self) -> list[DownloadProgress]:
        return list(self._progress.values())

    def cancel_download(self, download_id: str) -> bool:
        engine = self._engines.get(download_id)
        if engine is None:
            return False
        engine.cancel()
        return True

    def shutdown(self) -> None:
        self._shutdown_event.set()
        for engine in self._engines.values():
            engine.cancel()
        with self._slot_available:
            self._slot_available.notify_all()
        self._executor.shutdown(wait=False)
