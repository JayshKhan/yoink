from __future__ import annotations

import re

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Sign in to confirm you.re not a bot", re.I), "YouTube is requesting bot verification. Try again later or use a different IP."),
    (re.compile(r"(private video|video is private)", re.I), "This video is private."),
    (re.compile(r"(video unavailable|video has been removed)", re.I), "This video is unavailable or has been removed."),
    (re.compile(r"(age.restricted|age.gate|confirm your age)", re.I), "This video is age-restricted."),
    (re.compile(r"HTTP Error 429", re.I), "Rate limited by YouTube. Wait a minute and try again."),
    (re.compile(r"HTTP Error 403", re.I), "Access denied (403). The video may be region-locked."),
    (re.compile(r"HTTP Error 404", re.I), "Video not found (404). Check the URL."),
    (re.compile(r"(ffmpeg|ffprobe).*(not found|is not recognized)", re.I), "ffmpeg is not installed. Install it to merge video+audio."),
    (re.compile(r"(No space left on device|disk full|ENOSPC)", re.I), "Disk full. Free up space and try again."),
    (re.compile(r"(timed? ?out|TimeoutError|Read timed out)", re.I), "Connection timed out. Check your internet and try again."),
    (re.compile(r"(network|connection|ConnectionError|URLError)", re.I), "Network error. Check your internet connection."),
    (re.compile(r"Unsupported URL", re.I), "Unsupported URL. Only YouTube links are supported."),
    (re.compile(r"is not a valid URL", re.I), "Invalid URL. Paste a valid YouTube link."),
    (re.compile(r"live event will begin", re.I), "This is an upcoming live stream that hasn't started yet."),
    (re.compile(r"(members.only|premium)", re.I), "This video requires a membership or YouTube Premium."),
]


def friendly_error(raw: str) -> str:
    for pattern, message in _PATTERNS:
        if pattern.search(raw):
            return message
    if len(raw) > 120:
        return raw[:117] + "..."
    return raw
