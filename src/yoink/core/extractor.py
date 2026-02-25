from __future__ import annotations

import yt_dlp

from .models import FetchResult, FormatOption, PlaylistInfo, VideoInfo


class MetadataExtractor:
    """Wraps yt-dlp to extract video/playlist metadata without downloading."""

    _ydl_opts: dict = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    def fetch(self, url: str) -> FetchResult:
        """Single extraction that returns VideoInfo or PlaylistInfo."""
        opts = {**self._ydl_opts, "extract_flat": "in_playlist"}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None:
            raise ValueError(f"Could not extract info for {url}")

        if info.get("_type") == "playlist":
            videos = []
            for entry in info.get("entries", []) or []:
                if entry is None:
                    continue
                videos.append(
                    VideoInfo(
                        video_id=entry.get("id", ""),
                        title=entry.get("title", "Unknown"),
                        url=entry.get("url", ""),
                        duration=entry.get("duration"),
                    )
                )
            return PlaylistInfo(
                playlist_id=info.get("id", ""),
                title=info.get("title", "Unknown Playlist"),
                url=url,
                video_count=len(videos),
                videos=videos,
            )

        formats = self._parse_formats(info.get("formats", []))
        return VideoInfo(
            video_id=info.get("id", ""),
            title=info.get("title", "Unknown"),
            url=url,
            duration=info.get("duration"),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
            view_count=info.get("view_count"),
            description=info.get("description"),
            formats=formats,
        )

    def extract_video_info(self, url: str) -> VideoInfo:
        with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None:
            raise ValueError(f"Could not extract info for {url}")
        formats = self._parse_formats(info.get("formats", []))
        return VideoInfo(
            video_id=info.get("id", ""),
            title=info.get("title", "Unknown"),
            url=url,
            duration=info.get("duration"),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
            view_count=info.get("view_count"),
            description=info.get("description"),
            formats=formats,
        )

    def extract_playlist_info(self, url: str) -> PlaylistInfo:
        opts = {**self._ydl_opts, "extract_flat": "in_playlist"}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None:
            raise ValueError(f"Could not extract playlist info for {url}")
        videos = []
        for entry in info.get("entries", []) or []:
            if entry is None:
                continue
            videos.append(
                VideoInfo(
                    video_id=entry.get("id", ""),
                    title=entry.get("title", "Unknown"),
                    url=entry.get("url", ""),
                    duration=entry.get("duration"),
                )
            )
        return PlaylistInfo(
            playlist_id=info.get("id", ""),
            title=info.get("title", "Unknown Playlist"),
            url=url,
            video_count=len(videos),
            videos=videos,
        )

    def extract_formats(self, url: str) -> list[FormatOption]:
        with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None:
            return []
        return self._parse_formats(info.get("formats", []))

    def is_playlist(self, url: str) -> bool:
        opts = {**self._ydl_opts, "extract_flat": "in_playlist"}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is None:
            return False
        return info.get("_type") == "playlist"

    def _parse_formats(self, raw_formats: list[dict]) -> list[FormatOption]:
        formats = []
        seen = set()
        for f in raw_formats:
            fmt_id = f.get("format_id", "")
            if fmt_id in seen:
                continue
            seen.add(fmt_id)

            vcodec = f.get("vcodec", "none") or "none"
            acodec = f.get("acodec", "none") or "none"
            has_video = vcodec != "none"
            has_audio = acodec != "none"

            resolution = ""
            if has_video:
                h = f.get("height")
                if h:
                    resolution = f"{h}p"

            formats.append(
                FormatOption(
                    format_id=fmt_id,
                    format_note=f.get("format_note", ""),
                    ext=f.get("ext", ""),
                    resolution=resolution,
                    filesize=f.get("filesize") or f.get("filesize_approx"),
                    vcodec=vcodec,
                    acodec=acodec,
                    has_video=has_video,
                    has_audio=has_audio,
                    fps=f.get("fps"),
                    tbr=f.get("tbr"),
                )
            )
        return self._deduplicate_formats(formats)

    def _deduplicate_formats(self, formats: list[FormatOption]) -> list[FormatOption]:
        """Keep the best format per resolution to reduce clutter."""
        best: dict[str, FormatOption] = {}
        audio_only: list[FormatOption] = []

        for f in formats:
            if not f.has_video and f.has_audio:
                audio_only.append(f)
                continue
            if not f.has_video:
                continue
            key = f.resolution or f.format_id
            existing = best.get(key)
            if existing is None or (f.tbr or 0) > (existing.tbr or 0):
                best[key] = f

        result = sorted(best.values(), key=lambda x: self._res_sort_key(x), reverse=True)
        if audio_only:
            best_audio = max(audio_only, key=lambda x: x.tbr or 0)
            result.append(best_audio)
        return result

    @staticmethod
    def _res_sort_key(f: FormatOption) -> int:
        if f.resolution and f.resolution.endswith("p"):
            try:
                return int(f.resolution[:-1])
            except ValueError:
                pass
        return 0
