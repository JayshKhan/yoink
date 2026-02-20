#!/usr/bin/env python3
"""yoink - grab videos off YouTube."""

import sys
from pathlib import Path

import yt_dlp

LOGO = """
  ╭──╮
  │▶ │  yoink
  ╰──╯  grab videos, fast
"""


def get_info(url: str) -> dict:
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        return ydl.extract_info(url, download=False)


def pick_formats(info: dict) -> list[dict]:
    """Return deduplicated, user-friendly format list."""
    seen = {}
    for f in info.get("formats", []):
        vcodec = f.get("vcodec", "none") or "none"
        acodec = f.get("acodec", "none") or "none"
        has_video = vcodec != "none"
        has_audio = acodec != "none"
        if not has_video:
            continue
        h = f.get("height")
        if not h:
            continue
        key = f"{h}p"
        tbr = f.get("tbr") or 0
        if key not in seen or tbr > (seen[key].get("tbr") or 0):
            seen[key] = {**f, "_has_audio": has_audio, "_label": key}

    return sorted(seen.values(), key=lambda x: x.get("height", 0), reverse=True)


def human_size(nbytes):
    if nbytes is None:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def main():
    print(LOGO)
    url = sys.argv[1] if len(sys.argv) > 1 else input("YouTube URL: ").strip()
    if not url:
        print("No URL provided.")
        return

    print(f"Fetching info for: {url}")
    info = get_info(url)
    title = info.get("title", "Unknown")
    duration = info.get("duration", 0)
    uploader = info.get("uploader", "Unknown")
    m, s = divmod(duration or 0, 60)
    print(f"\n  Title:    {title}")
    print(f"  Uploader: {uploader}")
    print(f"  Duration: {m}:{s:02d}")

    formats = pick_formats(info)
    if not formats:
        print("\nNo video formats found. Downloading best available...")
        fmt_str = "best"
    else:
        print(f"\nAvailable formats:")
        for i, f in enumerate(formats):
            size = human_size(f.get("filesize") or f.get("filesize_approx"))
            ext = f.get("ext", "?")
            audio = "A+V" if f["_has_audio"] else "V only"
            print(f"  [{i}] {f['_label']:>6}  {ext:>5}  {size:>10}  ({audio})")

        choice = input(f"\nPick format [0-{len(formats)-1}] (default 0): ").strip()
        idx = int(choice) if choice.isdigit() and int(choice) < len(formats) else 0
        picked = formats[idx]

        if picked["_has_audio"]:
            fmt_str = picked["format_id"]
        else:
            fmt_str = f"{picked['format_id']}+bestaudio"
        print(f"\nSelected: {picked['_label']} ({picked.get('ext', '?')})")

    output_dir = Path.home() / "Downloads"
    output_dir.mkdir(exist_ok=True)

    print(f"Downloading to: {output_dir}\n")

    ydl_opts = {
        "format": fmt_str,
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "progress_hooks": [progress_hook],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("\nDone!")


def progress_hook(d):
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "?")
        speed = d.get("_speed_str", "?")
        eta = d.get("_eta_str", "?")
        print(f"\r  {pct}  {speed}  ETA: {eta}    ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  Download complete, processing...          ")


if __name__ == "__main__":
    main()
