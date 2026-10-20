import subprocess
import psutil
import os
from pynput.keyboard import Controller, Key

import media_session

keyboard = Controller()


def get_spotify_path():
    appdata = os.environ.get("APPDATA", "")
    path = os.path.join(appdata, "Spotify", "Spotify.exe")
    if os.path.exists(path):
        return path
    return None


def is_spotify_running():
    for process in psutil.process_iter(["name"]):
        try:
            if (
                process.info["name"]
                and process.info["name"].lower() == "spotify.exe"
            ):
                return True
        except Exception:
            pass

    return False


def open_spotify():
    if not is_spotify_running():
        path = get_spotify_path()
        if path:
            subprocess.Popen(path)


def tap(key):
    keyboard.press(key)
    keyboard.release(key)


def control_media(session_action, fallback_key):
    # Control whatever player is active (Spotify, browser, ...) directly;
    # fall back to a media key only if Windows reports no player at all
    try:
        if session_action() is not None:
            return
    except Exception as e:
        print("Media session error:", e)

    tap(fallback_key)


def has_media_player():
    try:
        return media_session.has_session()
    except Exception:
        return False


def play_pause():
    control_media(media_session.toggle_play_pause, Key.media_play_pause)


def next_track():
    control_media(media_session.skip_next, Key.media_next)


def previous_track():
    control_media(media_session.skip_previous, Key.media_previous)


def volume_up():
    tap(Key.media_volume_up)


def volume_down():
    tap(Key.media_volume_down)
