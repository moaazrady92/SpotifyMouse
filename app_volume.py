import threading

import comtypes
import psutil
import win32gui
import win32process
from pycaw.pycaw import AudioUtilities
from win32com.propsys import propsys, pscon

# Changes one app's own volume (its slider in the Windows Volume Mixer)
# instead of the whole PC's. Volume Mixer works per program, so for a
# browser this is the whole browser's volume, not a single tab.

_com_threads = threading.local()

# Media player ID (AppUserModelID) -> exe name, e.g. a hashed browser ID
# -> "zen.exe". Stable for a given install, so look each up only once.
_exe_cache = {}


def init_com():
    # Each thread that talks to Windows audio / UI Automation needs COM
    if getattr(_com_threads, "ready", False):
        return
    try:
        comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
    except OSError:
        pass  # COM already set up on this thread in another mode; still usable
    _com_threads.ready = True


def _window_app_id(hwnd):
    store = propsys.SHGetPropertyStoreForWindow(hwnd, propsys.IID_IPropertyStore)
    return store.GetValue(pscon.PKEY_AppUserModel_ID).GetValue()


def exe_for_source(source):
    if source in _exe_cache:
        return _exe_cache[source]

    # Desktop apps like Spotify report their exe name directly
    if source.lower().endswith(".exe"):
        _exe_cache[source] = source.lower()
        return _exe_cache[source]

    # Browsers and other apps report an ID; find a window carrying that
    # same ID and use its process
    found = []

    def check(hwnd, _):
        if found:
            return
        try:
            if _window_app_id(hwnd) == source:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                found.append(psutil.Process(pid).name().lower())
        except Exception:
            pass

    win32gui.EnumWindows(check, None)

    if not found:
        return None

    _exe_cache[source] = found[0]
    return found[0]


def _volumes_for_exe(exe):
    volumes = []

    for session in AudioUtilities.GetAllSessions():
        try:
            if session.Process and session.Process.name().lower() == exe:
                # Active sessions first, so the level is read from one
                # that's actually playing
                volumes.append((session.State != 1, session.SimpleAudioVolume))
        except Exception:
            pass

    return [volume for _, volume in sorted(volumes, key=lambda v: v[0])]


def change_app_volume(source, delta):
    """Change an app's volume by delta (0-1). Returns the new level in
    percent, or None if the app has no Volume Mixer entry."""
    init_com()

    exe = exe_for_source(source)
    if not exe:
        return None

    # A browser can have several audio sessions; keep them all in step
    volumes = _volumes_for_exe(exe)
    if not volumes:
        return None

    level = volumes[0].GetMasterVolume() + delta
    level = round(min(max(level, 0.0), 1.0), 2)

    for volume in volumes:
        volume.SetMasterVolume(level, None)
        if delta > 0:
            volume.SetMute(False, None)

    return round(level * 100)
