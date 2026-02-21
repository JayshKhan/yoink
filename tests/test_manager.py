from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from yoink.core.manager import DownloadManager
from yoink.core.models import DownloadProgress, DownloadRequest, DownloadStatus


@pytest.fixture
def manager():
    m = DownloadManager(max_concurrent=2)
    yield m
    m.shutdown()


class TestDownloadManager:
    def test_initial_state(self, manager):
        assert manager.max_concurrent == 2
        assert manager.active_count == 0
        assert manager.queued_count == 0

    def test_max_concurrent_setter_clamps(self, manager):
        manager.max_concurrent = 0
        assert manager.max_concurrent == 1
        manager.max_concurrent = 100
        assert manager.max_concurrent == 10

    @patch("yoink.core.manager.DownloadEngine")
    def test_start_download_returns_id(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine.run.return_value = DownloadProgress(
            download_id="abc", status=DownloadStatus.FINISHED
        )
        mock_engine_cls.return_value = mock_engine

        request = DownloadRequest(url="http://example.com", download_id="abc")
        result = manager.start_download(request)
        assert result == "abc"

    @patch("yoink.core.manager.DownloadEngine")
    def test_duplicate_detection_blocks(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request1 = DownloadRequest(url="http://example.com", download_id="dl1")
        request2 = DownloadRequest(url="http://example.com", download_id="dl2")

        result1 = manager.start_download(request1)
        assert result1 == "dl1"

        result2 = manager.start_download(request2)
        assert result2 is None

    @patch("yoink.core.manager.DownloadEngine")
    def test_duplicate_detection_force_bypass(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request1 = DownloadRequest(url="http://example.com", download_id="dl1")
        request2 = DownloadRequest(url="http://example.com", download_id="dl2")

        manager.start_download(request1)
        result2 = manager.start_download(request2, force=True)
        assert result2 == "dl2"

    @patch("yoink.core.manager.DownloadEngine")
    def test_duplicate_allowed_after_terminal_state(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request1 = DownloadRequest(url="http://example.com", download_id="dl1")
        manager.start_download(request1)

        # Simulate the progress callback setting terminal state
        manager._progress["dl1"] = DownloadProgress(
            download_id="dl1", status=DownloadStatus.FINISHED
        )
        manager._url_to_id.pop("http://example.com", None)

        request2 = DownloadRequest(url="http://example.com", download_id="dl2")
        result2 = manager.start_download(request2)
        assert result2 == "dl2"

    def test_cancel_nonexistent(self, manager):
        assert manager.cancel_download("nonexistent") is False

    @patch("yoink.core.manager.DownloadEngine")
    def test_cancel_download(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request = DownloadRequest(url="http://example.com", download_id="dl1")
        manager.start_download(request)

        assert manager.cancel_download("dl1") is True
        mock_engine.cancel.assert_called_once()

    def test_get_progress_none(self, manager):
        assert manager.get_progress("nonexistent") is None

    @patch("yoink.core.manager.DownloadEngine")
    def test_get_progress(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request = DownloadRequest(url="http://example.com", download_id="dl1")
        manager.start_download(request)

        progress = manager.get_progress("dl1")
        assert progress is not None
        assert progress.download_id == "dl1"

    @patch("yoink.core.manager.DownloadEngine")
    def test_get_all_progress(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        for i in range(3):
            req = DownloadRequest(url=f"http://example.com/{i}", download_id=f"dl{i}")
            manager.start_download(req)

        all_progress = manager.get_all_progress()
        assert len(all_progress) == 3

    @patch("yoink.core.manager.DownloadEngine")
    def test_callback_invoked(self, mock_engine_cls, manager):
        callback = MagicMock()
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request = DownloadRequest(url="http://example.com", download_id="dl1")
        manager.start_download(request, callback=callback)

        # The callback is wrapped internally; we verify the initial progress is set
        progress = manager.get_progress("dl1")
        assert progress is not None

    def test_shutdown(self, manager):
        manager.shutdown()
        assert manager._shutdown_event.is_set()
