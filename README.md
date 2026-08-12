# yt-dlp-tui

Convenient wrapper around `yt-dlp`. Tested with Ghostty on MacOS Tahoe 26.x.

## Installation (?)

```zsh
uv tool install --editable .
```

This creates a symlink `~/.local/bin/yt-dlp-tui` to a dedicated virtual environment (`~/.local/share/uv/tools/yt-dlp-tui`) that points to this source code. This isn't a proper installation, but works well enough for a mini-project.

## Development

```zsh
# Lint & format
uv run ruff check . --fix
```

## Backlog

- [x] Show destination directory
- [ ] "Loading" screen with timeout
- [ ] Configuration for destination directory
- [ ] Better menu for general configuration (e.g., disabling format filter)
- [ ] Progress indication during download
