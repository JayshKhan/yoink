from __future__ import annotations

import pytest

from yoink.core.errors import friendly_error


class TestFriendlyError:
    def test_bot_check(self):
        msg = friendly_error("Sign in to confirm you're not a bot")
        assert "bot verification" in msg

    def test_private_video(self):
        msg = friendly_error("This video is private")
        assert "private" in msg.lower()

    def test_unavailable(self):
        msg = friendly_error("Video unavailable")
        assert "unavailable" in msg.lower()

    def test_age_restricted(self):
        msg = friendly_error("This content is age-restricted")
        assert "age-restricted" in msg.lower()

    def test_429(self):
        msg = friendly_error("HTTP Error 429: Too Many Requests")
        assert "Rate limited" in msg

    def test_403(self):
        msg = friendly_error("HTTP Error 403: Forbidden")
        assert "403" in msg

    def test_404(self):
        msg = friendly_error("HTTP Error 404: Not Found")
        assert "404" in msg

    def test_ffmpeg_missing(self):
        msg = friendly_error("ffmpeg not found, please install")
        assert "ffmpeg" in msg.lower()

    def test_disk_full(self):
        msg = friendly_error("[Errno 28] No space left on device")
        assert "Disk full" in msg

    def test_timeout(self):
        msg = friendly_error("Read timed out")
        assert "timed out" in msg.lower()

    def test_network(self):
        msg = friendly_error("ConnectionError: failed to connect")
        assert "Network" in msg or "internet" in msg.lower()

    def test_unsupported_url(self):
        msg = friendly_error("Unsupported URL: http://example.com")
        assert "Unsupported" in msg

    def test_invalid_url(self):
        msg = friendly_error("'notaurl' is not a valid URL")
        assert "Invalid" in msg

    def test_live_event(self):
        msg = friendly_error("This live event will begin in 2 hours")
        assert "live stream" in msg.lower()

    def test_members_only(self):
        msg = friendly_error("This video is members-only content")
        assert "membership" in msg.lower()

    def test_unknown_short(self):
        msg = friendly_error("Some unknown error")
        assert msg == "Some unknown error"

    def test_unknown_truncated(self):
        long_msg = "x" * 200
        msg = friendly_error(long_msg)
        assert len(msg) == 120
        assert msg.endswith("...")
