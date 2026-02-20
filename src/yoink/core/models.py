from __future__ import annotations

import uuid
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class DownloadStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    FINISHED = "finished"
    ERROR = "error"
    CANCELLED = "cancelled"


class FormatOption(BaseModel):
    format_id: str
    format_note: str = ""
    ext: str = ""
    resolution: str = ""
    filesize: int | None = None
    vcodec: str = ""
    acodec: str = ""
    has_video: bool = False
    has_audio: bool = False
    fps: float | None = None
    tbr: float | None = None

    @property
    def display_name(self) -> str:
        parts = []
        if self.resolution:
            parts.append(self.resolution)
        if self.format_note:
            parts.append(self.format_note)
        if self.ext:
            parts.append(self.ext.upper())
        if self.filesize:
            parts.append(self._human_size(self.filesize))
        return " | ".join(parts) if parts else self.format_id

    @staticmethod
    def _human_size(nbytes: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if abs(nbytes) < 1024:
                return f"{nbytes:.1f} {unit}"
            nbytes /= 1024  # type: ignore[assignment]
        return f"{nbytes:.1f} TB"


class VideoInfo(BaseModel):
    video_id: str
    title: str
    url: str
    duration: int | None = None
    thumbnail: str | None = None
    uploader: str | None = None
    view_count: int | None = None
    description: str | None = None
    formats: list[FormatOption] = Field(default_factory=list)

    @property
    def duration_display(self) -> str:
        if self.duration is None:
            return "Unknown"
        m, s = divmod(self.duration, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


class PlaylistInfo(BaseModel):
    playlist_id: str
    title: str
    url: str
    video_count: int = 0
    videos: list[VideoInfo] = Field(default_factory=list)


class DownloadProgress(BaseModel):
    download_id: str
    status: DownloadStatus = DownloadStatus.QUEUED
    title: str = ""
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: float = 0.0
    eta: int | None = None
    percent: float = 0.0
    error: str | None = None

    @property
    def speed_display(self) -> str:
        if self.speed <= 0:
            return ""
        for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
            if abs(self.speed) < 1024:
                return f"{self.speed:.1f} {unit}"
            self.speed /= 1024
        return f"{self.speed:.1f} TB/s"

    @property
    def eta_display(self) -> str:
        if self.eta is None or self.eta < 0:
            return ""
        m, s = divmod(self.eta, 60)
        if m:
            return f"{m}m {s}s"
        return f"{s}s"


class DownloadRequest(BaseModel):
    url: str
    format_string: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    output_dir: str = str(Path.home() / "Downloads")
    output_template: str = "%(title)s.%(ext)s"
    download_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
