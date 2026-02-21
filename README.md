<p align="center">
  <img src="src/yoink/assets/yoink.png" alt="yoink" width="280">
</p>

<h1 align="center">yoink</h1>

<p align="center">
  <b>grab videos, fast</b><br>
  <sub>A no-nonsense YouTube downloader with a slick terminal UI <em>and</em> an MCP server so your AI assistant can yoink videos too.</sub>
</p>

<p align="center">
  <a href="#-quick-start"><img src="https://img.shields.io/badge/python-3.10+-3670A0?style=flat-square&logo=python&logoColor=ffdd54" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/yt-dlp/yt-dlp"><img src="https://img.shields.io/badge/powered%20by-yt--dlp-red?style=flat-square" alt="Powered by yt-dlp"></a>
  <a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/TUI-Textual-blueviolet?style=flat-square" alt="Textual"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-enabled-orange?style=flat-square" alt="MCP"></a>
</p>

<p align="center">
  <code>pip install yoink</code>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<code>uv run yoink</code>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<a href="#-mcp-server">MCP Server</a>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<a href="#-architecture">Docs</a>
</p>

---

<br>

<table>
<tr>
<td width="55%" valign="top">

### Three ways to yoink

&nbsp;&nbsp;**TUI** &mdash; Beautiful interactive terminal app. Paste a URL, pick a quality, hit download. Progress bars, speed stats, the works.

&nbsp;&nbsp;**MCP** &mdash; Expose download tools to AI assistants like Claude. Let your AI yoink videos for you.

&nbsp;&nbsp;**CLI** &mdash; Just a script. `python download.py <url>` and done.

All three share the same core engine powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

</td>
<td width="45%" valign="top">

### Highlights

- &nbsp;Concurrent downloads (up to 10)
- &nbsp;Playlist support with search/filter
- &nbsp;Quality selector &mdash; 1080p to audio-only
- &nbsp;Audio-only &amp; MP3 conversion
- &nbsp;Subtitle downloads
- &nbsp;Speed limiting
- &nbsp;Retry failed downloads
- &nbsp;Open folder on complete
- &nbsp;Friendly error messages
- &nbsp;Keyboard shortcuts

</td>
</tr>
</table>

<br>

## &#9889; Quick Start

```bash
git clone https://github.com/yourname/yoink.git
cd yoink
uv sync
uv run yoink
```

That's it. Paste a YouTube URL, pick your quality, download.

> [!TIP]
> Install **ffmpeg** for best results &mdash; it's needed to merge separate video+audio streams into a single file.
> ```
> brew install ffmpeg          # macOS
> sudo apt install ffmpeg      # Ubuntu/Debian
> ```

<br>

## &#127916; TUI Mode

```bash
uv run yoink              # default: 3 concurrent downloads
uv run yoink -j 5         # or up to 10
```

<table>
<tr>
<td>

**Keyboard shortcuts**

| Key | Action |
|-----|--------|
| <kbd>/</kbd> | Focus URL input |
| <kbd>d</kbd> | Start download |
| <kbd>r</kbd> | Retry last failed |
| <kbd>a</kbd> | Select all (playlist) |
| <kbd>n</kbd> | Select none (playlist) |
| <kbd>q</kbd> | Quit |

</td>
<td>

**Download features**

| Feature | Details |
|---------|---------|
| Output dir | Editable path below URL bar |
| Speed limit | Set in queue header (e.g. `5M`) |
| Subtitles | Checkbox &mdash; auto + manual subs |
| MP3 convert | Checkbox &mdash; uses ffmpeg |
| Filename template | Customizable in Advanced Settings |
| Retry | One click on failed downloads |
| Open folder | One click on finished downloads |

</td>
</tr>
</table>

<br>

## &#129302; MCP Server

```bash
uv run yoink-mcp
```

Exposes **7 tools** over STDIO for AI assistants:

| Tool | What it does |
|------|-------------|
| `get_video_info` | Fetch title, duration, formats |
| `get_playlist_info` | List all videos in a playlist |
| `get_formats` | Available qualities for a URL |
| `start_download` | Start downloading, get a tracking ID |
| `list_downloads` | See all downloads + progress |
| `get_download_progress` | Check on a specific download |
| `cancel_download` | Stop a download |

<details>
<summary><b>Claude Desktop configuration</b></summary>

<br>

Add to `claude_desktop_config.json`:

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

</details>

<br>

## &#128736; Architecture

```
src/yoink/
├── core/              # The engine room
│   ├── models.py      # Pydantic models shared everywhere
│   ├── errors.py      # Friendly error translation
│   ├── extractor.py   # yt-dlp metadata extraction
│   ├── engine.py      # Single download with progress hooks
│   └── manager.py     # Concurrent download orchestration
├── mcp_server/        # AI-friendly tools
│   └── server.py      # FastMCP with 7 tools
└── tui/               # The pretty terminal UI
    ├── app.py         # Main Textual app
    ├── screens/       # Main screen, format picker modal
    ├── widgets/       # URL bar, video panel, playlist, queue
    └── styles/        # Textual CSS
```

<details>
<summary><b>Key design decisions</b></summary>

<br>

- yt-dlp is synchronous &rarr; each download runs in its own thread via `ThreadPoolExecutor`
- FIFO dispatcher thread ensures downloads start in submission order
- Progress hooks are rate-limited to 100ms to keep the UI smooth
- Playlists use `extract_flat` for speed &mdash; no fetching full metadata for 500 videos upfront
- Pydantic models everywhere = clean contracts between core / TUI / MCP
- Duplicate URL detection prevents double-downloading the same video
- Cancellation via `threading.Event` checked in progress hooks

</details>

<br>

## &#128230; Dependencies

| Package | Why |
|---------|-----|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The extraction & download engine |
| [Textual](https://textual.textualize.io/) | Terminal UI framework |
| [Pydantic](https://docs.pydantic.dev/) | Data models & validation |
| [MCP SDK](https://modelcontextprotocol.io/) | AI tool server protocol |

**Dev dependencies:** `pytest` &mdash; install with `uv sync --extra dev`

<br>

## &#128295; Development

```bash
uv sync --extra dev       # install with test deps
uv run pytest tests/ -v   # run the test suite
uv run yoink              # test the TUI
uv run yoink-mcp          # test the MCP server
```

<br>

## &#128196; License

[MIT](LICENSE) &mdash; do whatever you want with it. Yoink responsibly.

<br>

<p align="center">
  <sub>Built with <a href="https://textual.textualize.io/">Textual</a> and <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a></sub>
</p>
