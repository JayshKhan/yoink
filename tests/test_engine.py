from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from yoink.core.engine import DownloadCancelled, DownloadEngine
from yoink.core.models import DownloadProgress, DownloadRequest, DownloadStatus


@pytest.fixture
def dl_request():
    return DownloadRequest(
        url="https://www.youtube.com/watch?v=test123",
        download_id="test_dl",
        output_dir="/tmp/yoink_test",
    )


class TestDownloadEngine:
    def test_initial_state(self, dl_request):
        engine = DownloadEngine(dl_request)
        assert engine.is_cancelled is False
        assert engine._progress.status == DownloadStatus.QUEUED

    def test_cancel(self, dl_request):
        engine = DownloadEngine(dl_request)
        engine.cancel()
        assert engine.is_cancelled is True

    @patch("yoink.core.engine.yt_dlp.YoutubeDL")
    def test_successful_download(self, mock_ydl_cls, dl_request):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test Video"}
        mock_ydl.download.return_value = None

        progress_updates = []
        engine = DownloadEngine(dl_request, callback=progress_updates.append)
        result = engine.run()

        assert result.status == DownloadStatus.FINISHED
        assert result.percent == 100.0
        assert result.title == "Test Video"
        assert len(progress_updates) > 0

    @patch("yoink.core.engine.yt_dlp.YoutubeDL")
    def test_download_error(self, mock_ydl_cls, dl_request):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("HTTP Error 429")

        progress_updates = []
        engine = DownloadEngine(dl_request, callback=progress_updates.append)
        result = engine.run()

        assert result.status == DownloadStatus.ERROR
        assert "Rate limited" in result.error

    @patch("yoink.core.engine.yt_dlp.YoutubeDL")
    def test_download_cancelled(self, mock_ydl_cls, dl_request):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test"}

        def cancel_during_download(urls):
            engine.cancel()
            raise DownloadCancelled()

        mock_ydl.download.side_effect = cancel_during_download

        engine = DownloadEngine(dl_request)
        result = engine.run()
        assert result.status == DownloadStatus.CANCELLED

    def test_progress_hook_downloading(self, dl_request):
        progress_updates = []
        engine = DownloadEngine(dl_request, callback=progress_updates.append)
        engine._last_callback_time = 0

        engine._progress_hook({
            "status": "downloading",
            "downloaded_bytes": 5000,
            "total_bytes": 10000,
            "speed": 1024.0,
            "eta": 5,
        })

        assert engine._progress.status == DownloadStatus.DOWNLOADING
        assert engine._progress.downloaded_bytes == 5000
        assert engine._progress.total_bytes == 10000
        assert engine._progress.percent == pytest.approx(50.0)

    def test_progress_hook_finished(self, dl_request):
        engine = DownloadEngine(dl_request)
        engine._progress_hook({
            "status": "finished",
            "filename": "/tmp/test.mp4",
        })

        assert engine._progress.status == DownloadStatus.MERGING
        assert engine._progress.percent == 100.0
        assert engine._progress.output_path == "/tmp/test.mp4"

    def test_progress_hook_cancelled_raises(self, dl_request):
        engine = DownloadEngine(dl_request)
        engine.cancel()

        with pytest.raises(DownloadCancelled):
            engine._progress_hook({"status": "downloading"})

    def test_postprocessor_hook_captures_filepath(self, dl_request):
        engine = DownloadEngine(dl_request)
        engine._postprocessor_hook({
            "status": "finished",
            "info_dict": {"filepath": "/tmp/final.mp4"},
        })
        assert engine._progress.output_path == "/tmp/final.mp4"

    @patch("yoink.core.engine.yt_dlp.YoutubeDL")
    def test_speed_limit_option(self, mock_ydl_cls, dl_request):
        req = dl_request.model_copy(update={"speed_limit": 1024 * 1024})
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test"}

        engine = DownloadEngine(req)
        engine.run()

        opts = mock_ydl_cls.call_args[0][0]
        assert opts["ratelimit"] == 1024 * 1024

    @patch("yoink.core.engine.yt_dlp.YoutubeDL")
    def test_subtitle_options(self, mock_ydl_cls, dl_request):
        req = dl_request.model_copy(update={"download_subtitles": True, "subtitle_lang": "fr"})
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test"}

        engine = DownloadEngine(req)
        engine.run()

        opts = mock_ydl_cls.call_args[0][0]
        assert opts["writesubtitles"] is True
        assert opts["writeautomaticsub"] is True
        assert opts["subtitleslangs"] == ["fr"]

    @patch("yoink.core.engine.yt_dlp.YoutubeDL")
    def test_mp3_conversion_options(self, mock_ydl_cls, dl_request):
        req = dl_request.model_copy(update={"convert_to_mp3": True})
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"title": "Test"}

        engine = DownloadEngine(req)
        engine.run()

        opts = mock_ydl_cls.call_args[0][0]
        assert "bestaudio" in opts["format"]
        pp = opts["postprocessors"]
        assert any(p["key"] == "FFmpegExtractAudio" for p in pp)

    def test_emit_progress_throttle(self, dl_request):
        updates = []
        engine = DownloadEngine(dl_request, callback=updates.append)

        engine._emit_progress(force=False)
        count_after_first = len(updates)

        engine._emit_progress(force=False)
        assert len(updates) == count_after_first

        engine._emit_progress(force=True)
        assert len(updates) == count_after_first + 1

    def test_no_callback(self, dl_request):
        engine = DownloadEngine(dl_request, callback=None)
        engine._emit_progress(force=True)
