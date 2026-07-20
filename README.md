# SpotifyMouse

A lightweight Windows app that lets you control Spotify with your mouse buttons and displays a floating "Now Playing" widget with album art.

## Features

- **Mouse 4** — Next track (hold to skip) / Open Spotify if not running
- **Mouse 5** — Play / Pause
- **Middle click** (hold) — Previous track
- **Mouse 4 + Scroll** — Volume control
- **Floating widget** — Shows current song, artist, album art, clock, and battery
- **System tray icon** — Show/hide widget, exit app
- Album art background color dynamically matches album cover

## Installation

1. Download `SpotifyMouse.exe` from [Releases](https://github.com/yourusername/SpotifyMouse/releases)
2. Run it — no installation needed
3. Spotify will auto-detect from `%APPDATA%\Spotify`

## Building from Source

```bash
pip install -r requirements.txt
pyinstaller spotify_mouse.spec
```

The exe will be in `dist/SpotifyMouse.exe`.

## Tech Stack

- **Python 3.13** + **PyQt6** (GUI)
- **pynput** (mouse listener)
- **pywin32** (Spotify window detection)
- **Deezer API** (album art)

## License

MIT
