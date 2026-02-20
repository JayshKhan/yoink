from __future__ import annotations

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from .engine import DownloadEngine
from .extractor import MetadataExtractor
from .models import (
    DownloadProgress,
    DownloadRequest,
    FormatOption,
    PlaylistInfo,
    VideoInfo,
)


class DownloadManager:
    """Orchestrates concurrent downloads and metadata extraction."""

    def __init__(self, max_concurrent: int = 3):
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._extractor = MetadataExtractor()
        self._engines: dict[str, DownloadEngine] = {}
        self._progress: dict[str, DownloadProgress] = {}

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
    ) -> str:
        download_id = request.download_id

        def _on_progress(progress: DownloadProgress) -> None:
            self._progress[download_id] = progress
            if callback:
                callback(progress)

        engine = DownloadEngine(request, callback=_on_progress)
        self._engines[download_id] = engine
        self._progress[download_id] = DownloadProgress(download_id=download_id)
        self._executor.submit(engine.run)
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
        for engine in self._engines.values():
            engine.cancel()
        self._executor.shutdown(wait=False)
