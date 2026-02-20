<p align="center">
  <img src="src/yoink/assets/yoink.png" alt="yoink" width="280">
</p>

<h3 align="center">grab videos, fast</h3>

<p align="center">
  A no-nonsense YouTube downloader with a slick terminal UI<br>
  <em>and</em> an MCP server so your AI assistant can yoink videos too.
</p>

<p align="center">
  <code>pip install yoink</code>&nbsp;&nbsp;·&nbsp;&nbsp;<code>uv run yoink</code>&nbsp;&nbsp;·&nbsp;&nbsp;Python 3.10+
</p>

---

## What is this?

**yoink** does one thing well: it grabs videos off YouTube.

- **TUI mode** — A beautiful interactive terminal app. Paste a URL, pick a quality, hit download. Progress bars, speed stats, the works.
- **MCP mode** — Expose download tools to AI assistants like Claude Desktop. Let your AI yoink videos for you.
- **CLI mode** — Just a script. No fancy UI. `python download.py <url>` and done.

All three share the same battle-tested core engine powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Quick Start

```bash
# Install
git clone https://github.com/yourname/yoink.git
cd yoink
uv sync

# Launch the TUI
uv run yoink
```

That's it. Paste a YouTube URL, pick your quality, download.

## Usage

### TUI (the pretty one)

```bash
uv run yoink
```

What you get:
- Paste any YouTube URL → instant video info
- Quality selector dropdown (1080p, 720p, 480p, audio-only)
- Playlist support with checkbox selection — pick which videos you want
- Live progress bars with speed and ETA
- Up to 3 simultaneous downloads
- Cancel any download mid-flight

### MCP Server (for AI assistants)

```bash
uv run yoink-mcp
```

Exposes 7 tools over STDIO:

| Tool | What it does |
|------|-------------|
| `get_video_info` | Fetch title, duration, formats |
| `get_playlist_info` | List all videos in a playlist |
| `get_formats` | Available qualities for a URL |
| `start_download` | Start downloading, get a tracking ID |
| `list_downloads` | See all downloads + progress |
| `get_download_progress` | Check on a specific download |
| `cancel_download` | Stop a download |

Add to Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yoink": {
      "command": "uv",
      "args": ["--directory", "/path/to/yoink", "run", "yoink-mcp"]
    }
  }
}
```

Then just ask Claude: *"Download this video in 720p: https://youtube.com/watch?v=..."*

### Simple CLI (the no-frills one)

```bash
uv run python download.py "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

Shows formats, you pick a number, it downloads. No dependencies beyond yt-dlp.

## Architecture

```
src/yoink/
├── core/           # The engine room
│   ├── models.py   # Pydantic models shared everywhere
│   ├── extractor.py# yt-dlp metadata extraction
│   ├── engine.py   # Single download with progress hooks
│   └── manager.py  # Concurrent download orchestration
├── mcp_server/     # AI-friendly tools
│   └── server.py   # FastMCP with 7 tools
└── tui/            # The pretty terminal UI
    ├── app.py      # Main Textual app
    ├── logo.py     # ASCII art logo (auto-generated from PNG)
    ├── screens/    # Main screen, format picker modal
    ├── widgets/    # URL bar, video panel, playlist panel, download queue
    └── styles/     # Textual CSS
```

**Key design decisions:**
- yt-dlp is synchronous → each download runs in its own thread via `ThreadPoolExecutor(max_workers=3)`
- Progress hooks are rate-limited to 100ms to keep the UI smooth
- Playlists use `extract_flat` for speed — no fetching full metadata for 500 videos upfront
- Pydantic models everywhere = clean contracts between core/TUI/MCP

## Requirements

- **Python 3.10+**
- **ffmpeg** (recommended) — needed to merge separate video+audio streams into a single file. Without it, some quality options won't work. Install via `brew install ffmpeg` or your package manager.

## Dependencies

| Package | Why |
|---------|-----|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The extraction & download engine |
| [Textual](https://textual.textualize.io/) | Terminal UI framework |
| [Pydantic](https://docs.pydantic.dev/) | Data models |
| [MCP SDK](https://modelcontextprotocol.io/) | AI tool server |

## License

Do whatever you want with it. Yoink responsibly.
