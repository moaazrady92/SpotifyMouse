import subprocess
import psutil
import os
from pynput.keyboard import Controller, Key

import app_volume
import in_app_volume
import media_session
import ytmusic_bridge

keyboard = Controller()

VOLUME_STEP = 0.05


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


def change_volume(delta, fallback_key):
    # Change the playing app's volume, best option first:
    #   1. its own in-app slider (Spotify, or YouTube Music via the userscript)
    #   2. its Volume Mixer slider (browsers and everything else)
    #   3. the PC volume
    # Returns the new volume in percent, or None for PC volume.
    try:
        source = media_session.get_target_source()
        if source:
            app_volume.init_com()
            exe = app_volume.exe_for_source(source)

            if exe and in_app_volume.supports(exe):
                level = in_app_volume.change_volume(exe, delta)
                if level is not None:
                    return level

            # A browser is playing and a YouTube Music tab says it's the one
            elif ytmusic_bridge.is_active():
                handled, level = ytmusic_bridge.change_volume(round(delta * 100))
                if handled:
                    return level

            level = app_volume.change_app_volume(source, delta)
            if level is not None:
                return level
    except Exception as e:
        print("App volume error:", e)

    tap(fallback_key)
    return None


def volume_up():
    return change_volume(VOLUME_STEP, Key.media_volume_up)


def volume_down():
    return change_volume(-VOLUME_STEP, Key.media_volume_down)
