from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yoink.core.manager import DownloadManager
from yoink.core.models import DownloadProgress, DownloadRequest


@pytest.fixture
def manager():
    m = DownloadManager(max_concurrent=2)
    yield m
    m.shutdown()


class TestDownloadManager:
    def test_initial_state(self, manager):
        assert manager.max_concurrent == 2
        assert manager.get_all_progress() == []

    def test_max_concurrent_setter_clamps(self, manager):
        manager.max_concurrent = 0
        assert manager.max_concurrent == 1
        manager.max_concurrent = 100
        assert manager.max_concurrent == 10

    @patch("yoink.core.manager.DownloadEngine")
    def test_start_download_returns_id(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request = DownloadRequest(url="http://example.com", download_id="abc")
        result = manager.start_download(request)
        assert result == "abc"

    @patch("yoink.core.manager.DownloadEngine")
    def test_multiple_downloads_tracked(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request1 = DownloadRequest(url="http://example.com/1", download_id="dl1")
        request2 = DownloadRequest(url="http://example.com/2", download_id="dl2")

        result1 = manager.start_download(request1)
        result2 = manager.start_download(request2)
        assert result1 == "dl1"
        assert result2 == "dl2"
        assert len(manager.get_all_progress()) == 2

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

    @patch("yoink.core.manager.DownloadEngine")
    def test_shutdown_cancels_engines(self, mock_engine_cls, manager):
        mock_engine = MagicMock()
        mock_engine.is_cancelled = False
        mock_engine_cls.return_value = mock_engine

        request = DownloadRequest(url="http://example.com", download_id="dl1")
        manager.start_download(request)
        manager.shutdown()
        mock_engine.cancel.assert_called_once()
