# SpotifyMouse

A lightweight Windows app that lets you control your music with your mouse buttons and displays a floating "Now Playing" widget with album art.

Works with any player Windows knows about — Spotify, YouTube Music or anything else in a browser, and other media apps. Commands go to whatever is playing.

## Features

- **Mouse 4** — Next track (hold to skip) / Open Spotify if nothing is playing
- **Mouse 5** — Play / Pause
- **Middle click** (hold) — Previous track
- **Mouse 4 + Scroll** — Volume of the playing app only, not the whole PC. For Spotify this moves Spotify's own volume slider (10% steps); for YouTube Music it moves YouTube Music's own slider (5% steps, needs the userscript below); for other apps it moves their Volume Mixer slider (in a browser that's the whole browser, not one tab)
- **Floating widget** — Shows current song, artist, album art, clock, and battery
- **System tray icon** — Show/hide widget, exit app
- **Starts with Windows** — the exe adds itself to startup on first run; untick "Start with Windows" in the tray menu to turn it off
- Album art background color dynamically matches album cover

## Installation

1. Download `SpotifyMouse.exe` from [Releases](https://github.com/moaazrady92/SpotifyMouse/releases)
2. Run it — no installation needed
3. Spotify will auto-detect from `%APPDATA%\Spotify`

### YouTube Music volume (optional)

A web page's volume slider can't be moved from outside the browser, so YouTube Music needs a small userscript:

1. Install the [Violentmonkey](https://violentmonkey.github.io/) extension in your browser (Zen/Firefox: from addons.mozilla.org).
2. With SpotifyMouse running, right-click its tray icon → **Install YouTube Music Volume Script**, or open `http://127.0.0.1:47821/spotify-mouse-ytmusic.user.js` in that browser.
3. Click **Install** on Violentmonkey's page, then reload any open YouTube Music tabs.

The script talks only to SpotifyMouse on your own PC (`127.0.0.1`). Without it, scrolling changes the browser's Volume Mixer volume instead.

## Building from Source

```bash
pip install -r requirements.txt
pyinstaller spotify_mouse.spec
```

The exe will be in `dist/SpotifyMouse.exe`.

## Tech Stack

- **Python 3.13** + **PyQt6** (GUI)
- **pynput** (mouse listener)
- **Windows media session API** via `winrt` (detects and controls any player)
- **pywin32** (single-instance guard)
- **Deezer API** (album art fallback)

