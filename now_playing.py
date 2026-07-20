import win32gui
import win32process
import psutil

def get_current_song():
    result = {}

    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if not title or " - " not in title:
            return

        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()

            # Strictly only Spotify, ignore browsers and everything else
            if process_name != "spotify.exe":
                return

            parts = title.split(" - ", 1)
            artist = parts[0].strip()
            song = parts[1].strip()

            # Extra check: ignore if it looks like a browser tab
            if any(x in title.lower() for x in ["youtube", "http", "www", ".com", "chrome", "firefox", "edge"]):
                return

            result["artist"] = artist
            result["title"] = song

        except Exception:
            pass

    win32gui.EnumWindows(callback, None)
    return result if result else None