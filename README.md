<p align="center">
  <img src="src/yoink/assets/yoink.png" alt="yoink - MCP YouTube downloader for AI assistants" width="280">
</p>

<h1 align="center">yoink</h1>

<p align="center">
  <b>MCP server that lets AI assistants download YouTube videos.</b><br>
  <sub>Give Claude, Cursor, or any MCP-compatible AI the ability to download YouTube videos, playlists, and audio through natural language. Also ships with a terminal UI for humans.</sub>
</p>

<p align="center">
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/MCP-enabled-orange?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiPjxwYXRoIGQ9Ik0xMiAyYTEwIDEwIDAgMSAwIDAgMjAgMTAgMTAgMCAwIDAgMC0yMHoiLz48cGF0aCBkPSJNOCAxMmg4Ii8+PHBhdGggZD0iTTEyIDh2OCIvPjwvc3ZnPg==&logoColor=white" alt="MCP Enabled"></a>
  <a href="https://pypi.org/project/yoink-yt/"><img src="https://img.shields.io/pypi/v/yoink-yt?style=for-the-badge&label=PyPI&color=blue" alt="PyPI"></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/python-3.10+-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="MIT License"></a>
</p>

<p align="center">
  <code>pip install yoink-yt</code>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<a href="#-mcp-setup-for-ai-assistants">MCP Setup</a>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<a href="#-terminal-ui-for-humans">Terminal UI</a>&nbsp;&nbsp;&middot;&nbsp;&nbsp;<a href="#-mcp-tools-api-reference">API Reference</a>
</p>

---

<br>

## What is yoink?

**yoink** is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that gives AI assistants like **Claude Desktop**, **Cursor**, **Windsurf**, and other MCP-compatible tools the ability to **download YouTube videos** on your behalf.

It also ships with a standalone **terminal UI (TUI)** for when you want to download videos yourself.

### The problem

Every YouTube downloader makes **you** do the work &mdash; find the URL, open a tool, pick a format, wait for it, rename the file, repeat.

### The yoink way

Just tell your AI assistant what you want:

> *"Download the latest 3Blue1Brown video in 720p"*
>
> *"Grab that playlist as audio-only MP3s"*
>
> *"Download this lecture with subtitles to my Desktop"*

Your AI handles the entire workflow &mdash; resolves the URL, picks the format, starts the download, tracks progress. No copy-pasting. No menus. Just ask.

<br>

## &#9889; Quick Start

```bash
pip install yoink-yt
```

<table>
<tr>
<td width="50%">

**For AI assistants (MCP server)**

```bash
yoink-mcp
```

Add to Claude Desktop, Cursor, or any MCP client &mdash; your AI gets 7 YouTube tools instantly.

</td>
<td width="50%">

**For humans (terminal UI)**

```bash
yoink
```

A full terminal UI with progress bars, quality picker, playlist support, and keyboard shortcuts.

</td>
</tr>
</table>

> [!TIP]
> Install **ffmpeg** for best results &mdash; needed to merge video+audio streams and convert to MP3.
> ```
> brew install ffmpeg          # macOS
> sudo apt install ffmpeg      # Ubuntu/Debian
> ```

<br>

## &#129302; MCP Setup for AI Assistants

yoink exposes **7 tools** via the [Model Context Protocol](https://modelcontextprotocol.io/) over STDIO, giving any MCP-compatible AI assistant full YouTube download capabilities.

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yoink": {
      "command": "yoink-mcp"
    }
  }
}
```

Restart Claude Desktop. Done &mdash; Claude can now download YouTube videos.

### Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "yoink": {
      "command": "yoink-mcp",
      "type": "stdio"
    }
  }
}
```

### Cursor / Windsurf / Other MCP Clients

Any MCP client that supports STDIO transport works. Point it at `yoink-mcp` as the command.

<details>
<summary><b>Using uv (from source instead of pip)</b></summary>

<br>

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

</details>

### Example prompts for your AI

| What you say | What yoink does |
|-------------|-----------------|
| *"Download this video: [url]"* | Downloads in best quality to ~/Downloads |
| *"Get the 720p version of [url]"* | Fetches formats, picks 720p, downloads |
| *"Download this playlist as audio"* | Gets playlist info, downloads each as audio |
| *"What formats are available for [url]?"* | Lists all quality options with file sizes |
| *"Cancel the download"* | Stops an in-progress download |
| *"What's the progress?"* | Shows status of all active downloads |
| *"Download [url] with subtitles"* | Downloads video + subtitle files |
| *"Convert [url] to MP3"* | Downloads audio and converts to MP3 |

<br>

## &#128268; MCP Tools API Reference

These are the tools your AI assistant gets access to when yoink is configured as an MCP server:

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_video_info` | Fetch video metadata (title, duration, uploader, available formats) | `url` |
| `get_playlist_info` | List all videos in a YouTube playlist | `url` |
| `get_formats` | List available download qualities with file sizes | `url` |
| `start_download` | Start downloading a video, returns a tracking ID | `url`, `format_string`, `output_dir` |
| `list_downloads` | Get progress of all active and completed downloads | &mdash; |
| `get_download_progress` | Check status of a specific download by ID | `download_id` |
| `cancel_download` | Cancel an active download | `download_id` |

> [!NOTE]
> **Duplicate detection** is built in &mdash; if a download is requested for a URL that's already being downloaded, yoink returns an error instead of starting a duplicate. This means your AI can safely retry without causing double-downloads.

<br>

## &#127916; Terminal UI for Humans

For when you want to download videos yourself. A full-featured TUI powered by [Textual](https://textual.textualize.io/).

```bash
yoink              # default: 3 concurrent downloads
yoink -j 5         # up to 10
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

**Features**

| Feature | Details |
|---------|---------|
| Quality picker | 1080p down to audio-only |
| Playlists | Search, filter, batch download |
| Audio-only | One-click, or convert to MP3 |
| Subtitles | Auto-generated + manual subs |
| Speed limit | e.g. `5M` for 5 MB/s cap |
| Output dir | Editable save path |
| Retry | One click on failed downloads |
| Open folder | One click on finished |

</td>
</tr>
</table>

<br>

## &#128736; Architecture

```
src/yoink/
├── core/              # Shared engine (used by both MCP + TUI)
│   ├── models.py      # Pydantic data models
│   ├── errors.py      # yt-dlp error → friendly message translation
│   ├── extractor.py   # YouTube metadata extraction via yt-dlp
│   ├── engine.py      # Single download executor with progress hooks
│   └── manager.py     # Concurrent download orchestration + duplicate detection
├── mcp_server/        # MCP interface for AI assistants
│   └── server.py      # FastMCP server with 7 tools over STDIO
└── tui/               # Terminal UI for humans
    ├── app.py         # Main Textual application
    ├── screens/       # Main screen, format picker modal
    ├── widgets/       # URL bar, video panel, playlist panel, download queue
    └── styles/        # Textual CSS styling
```

Both the MCP server and TUI are thin wrappers around the same core engine. The core handles all yt-dlp interaction, threading, progress tracking, and error handling.

<details>
<summary><b>Design decisions</b></summary>

<br>

- **Threading model:** yt-dlp is synchronous, so each download runs in its own thread via `ThreadPoolExecutor`. A FIFO dispatcher thread ensures downloads start in submission order.
- **Progress reporting:** Hooks are rate-limited to 100ms intervals to avoid callback floods in both MCP and TUI contexts.
- **Playlist optimization:** Uses `extract_flat` to avoid fetching full metadata for large playlists upfront.
- **Error handling:** Raw yt-dlp errors are pattern-matched against 15 common cases and translated to user-friendly messages.
- **Duplicate detection:** The download manager tracks active URLs and rejects duplicates at the engine level, with a `force` bypass for retries.
- **Cancellation:** Uses `threading.Event` checked in every progress hook callback for responsive cancellation.
- **Data contracts:** Pydantic models are shared across core, TUI, and MCP layers for type safety.

</details>

<br>

## &#128295; Development

```bash
git clone https://github.com/JayshKhan/yoink.git
cd yoink
uv sync --extra dev       # install with test deps
uv run pytest tests/ -v   # 84 tests
uv run yoink              # test the TUI
uv run yoink-mcp          # test the MCP server
```

<br>

## Frequently Asked Questions

<details>
<summary><b>What AI assistants work with yoink?</b></summary>

<br>

Any AI assistant that supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) over STDIO transport. This includes **Claude Desktop**, **Claude Code**, **Cursor**, **Windsurf**, and any custom MCP client.

</details>

<details>
<summary><b>Does it only work with YouTube?</b></summary>

<br>

yoink uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) under the hood, which supports thousands of sites. However, yoink is optimized and tested for YouTube. Other sites may work but are not officially supported.

</details>

<details>
<summary><b>Can I use the MCP server and TUI at the same time?</b></summary>

<br>

They are separate processes with separate download managers, so yes. They won't share state or conflict with each other.

</details>

<details>
<summary><b>Where do downloads go?</b></summary>

<br>

By default, `~/Downloads`. The MCP `start_download` tool accepts an `output_dir` parameter, and the TUI has an editable path below the URL bar.

</details>

<details>
<summary><b>What if ffmpeg is not installed?</b></summary>

<br>

You can still download videos, but some quality options that require merging separate video and audio streams won't work. MP3 conversion also requires ffmpeg.

</details>

<br>

## &#128196; License

[MIT](LICENSE) &mdash; do whatever you want with it. Yoink responsibly.

<br>

<p align="center">
  <sub>Powered by <a href="https://github.com/yt-dlp/yt-dlp">yt-dlp</a> &middot; UI by <a href="https://textual.textualize.io/">Textual</a> &middot; AI integration via <a href="https://modelcontextprotocol.io/">MCP</a></sub>
</p>
