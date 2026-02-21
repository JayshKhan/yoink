from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yoink.core.extractor import MetadataExtractor
from yoink.core.models import FormatOption


@pytest.fixture
def extractor():
    return MetadataExtractor()


class TestMetadataExtractor:
    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_extract_video_info(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            "id": "abc123",
            "title": "Test Video",
            "duration": 120,
            "uploader": "TestUser",
            "view_count": 1000,
            "formats": [
                {
                    "format_id": "137",
                    "format_note": "1080p",
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "acodec": "none",
                    "height": 1080,
                    "fps": 30,
                    "tbr": 5000,
                }
            ],
        }

        info = extractor.extract_video_info("http://example.com")
        assert info.video_id == "abc123"
        assert info.title == "Test Video"
        assert info.duration == 120
        assert len(info.formats) == 1
        assert info.formats[0].resolution == "1080p"

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_extract_video_info_none_raises(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None

        with pytest.raises(ValueError, match="Could not extract info"):
            extractor.extract_video_info("http://example.com")

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_extract_playlist_info(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            "id": "PL123",
            "title": "Test Playlist",
            "_type": "playlist",
            "entries": [
                {"id": "v1", "title": "Video 1", "url": "http://v1", "duration": 60},
                {"id": "v2", "title": "Video 2", "url": "http://v2", "duration": 120},
                None,  # should be skipped
            ],
        }

        info = extractor.extract_playlist_info("http://example.com")
        assert info.playlist_id == "PL123"
        assert info.title == "Test Playlist"
        assert info.video_count == 2
        assert len(info.videos) == 2

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_extract_playlist_info_none_raises(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None

        with pytest.raises(ValueError, match="Could not extract playlist info"):
            extractor.extract_playlist_info("http://example.com")

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_extract_formats_none(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None

        formats = extractor.extract_formats("http://example.com")
        assert formats == []

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_is_playlist_true(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"_type": "playlist"}

        assert extractor.is_playlist("http://example.com") is True

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_is_playlist_false(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"_type": "video"}

        assert extractor.is_playlist("http://example.com") is False

    @patch("yoink.core.extractor.yt_dlp.YoutubeDL")
    def test_is_playlist_none(self, mock_ydl_cls, extractor):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None

        assert extractor.is_playlist("http://example.com") is False


class TestFormatParsing:
    def test_parse_formats_dedup(self, extractor):
        raw = [
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "tbr": 5000},
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "tbr": 5000},
        ]
        result = extractor._parse_formats(raw)
        assert len(result) == 1

    def test_parse_formats_resolution(self, extractor):
        raw = [
            {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080, "tbr": 5000},
            {"format_id": "136", "vcodec": "avc1", "acodec": "none", "height": 720, "tbr": 3000},
        ]
        result = extractor._parse_formats(raw)
        assert result[0].resolution == "1080p"
        assert result[1].resolution == "720p"

    def test_parse_formats_audio_only(self, extractor):
        raw = [
            {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "tbr": 128},
        ]
        result = extractor._parse_formats(raw)
        assert len(result) == 1
        assert result[0].has_audio is True
        assert result[0].has_video is False

    def test_deduplicate_keeps_best_per_resolution(self, extractor):
        formats = [
            FormatOption(format_id="1", resolution="1080p", has_video=True, tbr=5000),
            FormatOption(format_id="2", resolution="1080p", has_video=True, tbr=8000),
            FormatOption(format_id="3", resolution="720p", has_video=True, tbr=3000),
        ]
        result = extractor._deduplicate_formats(formats)
        res_1080 = [f for f in result if f.resolution == "1080p"]
        assert len(res_1080) == 1
        assert res_1080[0].format_id == "2"  # higher tbr

    def test_res_sort_key(self):
        f1080 = FormatOption(format_id="1", resolution="1080p", has_video=True)
        f720 = FormatOption(format_id="2", resolution="720p", has_video=True)
        f_bad = FormatOption(format_id="3", resolution="unknown", has_video=True)

        assert MetadataExtractor._res_sort_key(f1080) == 1080
        assert MetadataExtractor._res_sort_key(f720) == 720
        assert MetadataExtractor._res_sort_key(f_bad) == 0
