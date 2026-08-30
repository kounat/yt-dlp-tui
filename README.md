# yt-dlp-tui

Terminal UI for `yt-dlp`, built with Textual. Tested with Ghostty on MacOS Tahoe 26.x.

Built as a foray into Terminal interfaces & for self-convenience to download YouTube videos.

## Installation (?)

```zsh
uv tool install --editable . --reinstall
```

This creates a symlink `~/.local/bin/yt-dlp-tui` to a dedicated virtual environment (`~/.local/share/uv/tools/yt-dlp-tui`) that points to this source code. This isn't a proper installation, but works well enough for a mini-project.

## Development

```zsh
# Lint & format
uv run ruff check . --fix
# Run the app
uv run yt-dlp-tui
```

## Backlog

- [x] Show destination directory
- [x] "Loading" screen with timeout
- [ ] Configuration for destination directory
- [ ] Better menu for general configuration (e.g., disabling format filter)
- [ ] Progress indication during download
