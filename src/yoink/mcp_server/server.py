from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from yoink.core.manager import DownloadManager
from yoink.core.models import DownloadRequest

mcp = FastMCP("Yoink")
manager = DownloadManager(max_concurrent=3)


@mcp.tool()
async def get_video_info(url: str) -> dict:
    """Fetch video metadata including title, duration, uploader, and available formats."""
    info = await manager.get_video_info(url)
    return info.model_dump()


@mcp.tool()
async def get_playlist_info(url: str) -> dict:
    """Fetch playlist metadata including all video titles and IDs."""
    info = await manager.get_playlist_info(url)
    return info.model_dump()


@mcp.tool()
async def get_formats(url: str) -> list[dict]:
    """List available download formats/qualities for a video URL."""
    formats = await manager.get_formats(url)
    return [f.model_dump() for f in formats]


@mcp.tool()
async def start_download(
    url: str,
    format_string: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    output_dir: str = str(Path.home() / "Downloads"),
) -> dict:
    """Start downloading a video. Returns a download_id for tracking progress."""
    request = DownloadRequest(
        url=url,
        format_string=format_string,
        output_dir=output_dir,
    )
    download_id = manager.start_download(request)
    if download_id is None:
        return {"error": "This URL is already being downloaded"}
    return {"download_id": download_id, "status": "started"}


@mcp.tool()
async def list_downloads() -> list[dict]:
    """List all downloads with their current status and progress."""
    return [p.model_dump() for p in manager.get_all_progress()]


@mcp.tool()
async def get_download_progress(download_id: str) -> dict:
    """Get the current progress of a specific download."""
    progress = manager.get_progress(download_id)
    if progress is None:
        return {"error": f"No download found with id {download_id}"}
    return progress.model_dump()


@mcp.tool()
async def cancel_download(download_id: str) -> dict:
    """Cancel an active download."""
    success = manager.cancel_download(download_id)
    if success:
        return {"status": "cancelled", "download_id": download_id}
    return {"error": f"No active download found with id {download_id}"}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
