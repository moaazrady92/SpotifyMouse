import os
import sys
import winreg

APP_NAME = "SpotifyMouse"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
SETTINGS_KEY = rf"Software\{APP_NAME}"


def is_frozen():
    return getattr(sys, "frozen", False)


def startup_command():
    if is_frozen():
        return f'"{sys.executable}"'

    # Running from source: use pythonw so no console window opens at login
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    script = os.path.abspath(sys.argv[0])
    return f'"{pythonw}" "{script}"'


def is_startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False


def set_startup(enabled):
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, startup_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, SETTINGS_KEY) as key:
        winreg.SetValueEx(key, "StartWithWindows", 0, winreg.REG_DWORD, int(enabled))


def wants_startup():
    # On by default; off only if the user unticked it in the tray menu
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, SETTINGS_KEY) as key:
            return bool(winreg.QueryValueEx(key, "StartWithWindows")[0])
    except FileNotFoundError:
        return True


def sync_startup():
    # Only the built exe registers itself automatically, so running from
    # source never overwrites the exe's startup entry. Re-registering on
    # every launch keeps the path right if the exe was moved.
    if is_frozen():
        set_startup(wants_startup())
