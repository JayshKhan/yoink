from __future__ import annotations

from pathlib import Path

import pytest

from yoink.core.models import (
    DownloadProgress,
    DownloadRequest,
    DownloadStatus,
    FormatOption,
    PlaylistInfo,
    VideoInfo,
)


class TestFormatOption:
    def test_display_name_full(self):
        fmt = FormatOption(
            format_id="137",
            resolution="1080p",
            format_note="Premium",
            ext="mp4",
            filesize=1024 * 1024 * 50,
        )
        name = fmt.display_name
        assert "1080p" in name
        assert "Premium" in name
        assert "MP4" in name

    def test_display_name_fallback(self):
        fmt = FormatOption(format_id="137")
        assert fmt.display_name == "137"

    def test_human_size_bytes(self):
        assert "500.0 B" == FormatOption._human_size(500)

    def test_human_size_kb(self):
        result = FormatOption._human_size(2048)
        assert "KB" in result

    def test_human_size_mb(self):
        result = FormatOption._human_size(1024 * 1024 * 5)
        assert "MB" in result

    def test_human_size_gb(self):
        result = FormatOption._human_size(1024**3 * 2)
        assert "GB" in result

    def test_human_size_tb(self):
        result = FormatOption._human_size(1024**4 * 3)
        assert "TB" in result


class TestVideoInfo:
    def test_duration_display_none(self):
        v = VideoInfo(video_id="abc", title="Test", url="http://example.com")
        assert v.duration_display == "Unknown"

    def test_duration_display_minutes(self):
        v = VideoInfo(video_id="abc", title="Test", url="http://example.com", duration=125)
        assert v.duration_display == "2:05"

    def test_duration_display_hours(self):
        v = VideoInfo(video_id="abc", title="Test", url="http://example.com", duration=3661)
        assert v.duration_display == "1:01:01"

    def test_duration_display_zero(self):
        v = VideoInfo(video_id="abc", title="Test", url="http://example.com", duration=0)
        assert v.duration_display == "0:00"


class TestPlaylistInfo:
    def test_defaults(self):
        p = PlaylistInfo(playlist_id="PL1", title="My List", url="http://example.com")
        assert p.video_count == 0
        assert p.videos == []


class TestDownloadProgress:
    def test_defaults(self):
        p = DownloadProgress(download_id="abc")
        assert p.status == DownloadStatus.QUEUED
        assert p.percent == 0.0
        assert p.output_path is None

    def test_speed_display_zero(self):
        p = DownloadProgress(download_id="abc", speed=0)
        assert p.speed_display == ""

    def test_speed_display_bytes(self):
        p = DownloadProgress(download_id="abc", speed=500.0)
        assert "B/s" in p.speed_display

    def test_speed_display_mb(self):
        p = DownloadProgress(download_id="abc", speed=5.0 * 1024 * 1024)
        assert "MB/s" in p.speed_display

    def test_eta_display_none(self):
        p = DownloadProgress(download_id="abc", eta=None)
        assert p.eta_display == ""

    def test_eta_display_negative(self):
        p = DownloadProgress(download_id="abc", eta=-1)
        assert p.eta_display == ""

    def test_eta_display_seconds(self):
        p = DownloadProgress(download_id="abc", eta=45)
        assert p.eta_display == "45s"

    def test_eta_display_minutes(self):
        p = DownloadProgress(download_id="abc", eta=125)
        assert "2m" in p.eta_display

    def test_size_display_both(self):
        p = DownloadProgress(
            download_id="abc",
            downloaded_bytes=1024 * 1024 * 10,
            total_bytes=1024 * 1024 * 100,
        )
        display = p.size_display
        assert "/" in display
        assert "MB" in display

    def test_size_display_downloaded_only(self):
        p = DownloadProgress(
            download_id="abc",
            downloaded_bytes=1024 * 500,
            total_bytes=0,
        )
        display = p.size_display
        assert "KB" in display

    def test_size_display_empty(self):
        p = DownloadProgress(download_id="abc")
        assert p.size_display == ""


class TestDownloadRequest:
    def test_defaults(self):
        r = DownloadRequest(url="http://example.com")
        assert r.output_dir == str(Path.home() / "Downloads")
        assert r.output_template == "%(title)s.%(ext)s"
        assert len(r.download_id) == 12
        assert r.speed_limit is None
        assert r.download_subtitles is False
        assert r.subtitle_lang == "en"
        assert r.convert_to_mp3 is False

    def test_unique_ids(self):
        r1 = DownloadRequest(url="http://example.com")
        r2 = DownloadRequest(url="http://example.com")
        assert r1.download_id != r2.download_id

    def test_custom_fields(self):
        r = DownloadRequest(
            url="http://example.com",
            speed_limit=1024 * 1024,
            download_subtitles=True,
            subtitle_lang="fr",
            convert_to_mp3=True,
        )
        assert r.speed_limit == 1024 * 1024
        assert r.download_subtitles is True
        assert r.subtitle_lang == "fr"
        assert r.convert_to_mp3 is True

    def test_model_copy_update(self):
        r = DownloadRequest(url="http://example.com", download_id="original")
        r2 = r.model_copy(update={"download_id": "new_id", "speed_limit": 5000})
        assert r2.download_id == "new_id"
        assert r2.speed_limit == 5000
        assert r2.url == r.url
