import subprocess
import psutil
import os
import keyboard


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



def play_pause():
    keyboard.send("play/pause media")


def next_track():
    keyboard.send("next track")


def previous_track():
    keyboard.send("previous track")


def volume_up():
    keyboard.send("volume up")


def volume_down():
    keyboard.send("volume down")