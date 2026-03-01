# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in yoink, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please email the maintainer directly or use [GitHub's private vulnerability reporting](https://github.com/JayshKhan/yoink/security/advisories/new).

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline

- **Acknowledgement**: within 48 hours
- **Initial assessment**: within 1 week
- **Fix or mitigation**: as soon as practical, depending on severity

## Scope

This policy covers the `yoink-yt` Python package published on PyPI, including:

- The MCP server (`yoink-mcp`)
- The terminal UI (`yoink`)
- All code in this repository

## Known considerations

- **yt-dlp dependency**: yoink relies on [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading. Security issues in yt-dlp should be reported to that project directly.
- **MCP server**: The MCP server executes download operations on the host machine. Users should only connect it to trusted MCP clients.
- **File system access**: Downloads are written to the local file system. Ensure the configured output directory has appropriate permissions.
