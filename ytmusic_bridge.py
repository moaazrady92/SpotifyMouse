import itertools
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# YouTube Music's volume slider lives inside the web page, where nothing
# outside the browser can move it. The userscript in ytmusic/ runs in the
# YouTube Music tab and long-polls this small server (on 127.0.0.1 only)
# for volume commands, then reports the slider's new level back.

PORT = 47821
POLL_SECONDS = 20
CONNECTED_GRACE = 3  # seconds a page counts as connected between polls

SCRIPT_NAME = "spotify-mouse-ytmusic.user.js"
SCRIPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ytmusic", SCRIPT_NAME)
SCRIPT_URL = f"http://127.0.0.1:{PORT}/{SCRIPT_NAME}"

_cond = threading.Condition()
_ids = itertools.count(1)
_pending = None  # (id, step) waiting for the page to pick up
_results = {}
_waiting_polls = 0
_last_seen = 0.0
_playing = False


def _seen(playing=None):
    global _last_seen, _playing
    _last_seen = time.monotonic()
    if playing is not None:
        _playing = playing


def is_active():
    """A YouTube Music tab is connected and playing."""
    with _cond:
        connected = _waiting_polls > 0 or time.monotonic() - _last_seen < CONNECTED_GRACE
        return connected and _playing


def change_volume(step, timeout=1.0):
    """Ask the YouTube Music tab to move its slider by step (0-100 scale).
    Returns (handled, level): handled is False if no tab is connected or
    it didn't answer; level is the slider's new value."""
    global _pending, _playing

    with _cond:
        if not is_active():
            return False, None

        command_id = next(_ids)
        _pending = (command_id, step)
        _cond.notify_all()

        deadline = time.monotonic() + timeout
        while command_id not in _results:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            _cond.wait(remaining)

        # Don't let an unanswered command fire later on another page
        if _pending and _pending[0] == command_id:
            _pending = None

        if command_id not in _results:
            # The tab was closed (its last poll can linger on the server);
            # treat it as gone until it reports in again
            _playing = False
            return False, None

        return True, _results.pop(command_id)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # no console in the built exe

    def _from_userscript(self):
        # Web pages can't send custom headers to another origin without a
        # CORS preflight (which this server never approves); the
        # userscript's GM_xmlhttpRequest can
        return self.headers.get("X-SpotifyMouse") == "1"

    def _reply(self, status, body=b"", content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        global _pending, _waiting_polls

        if self.path == "/" + SCRIPT_NAME:
            with open(SCRIPT_PATH, "rb") as f:
                return self._reply(200, f.read(), "text/javascript; charset=utf-8")

        if not self.path.startswith("/ytmusic/next") or not self._from_userscript():
            return self._reply(404)

        playing = "playing=1" in self.path

        with _cond:
            _seen(playing)
            _waiting_polls += 1
            try:
                deadline = time.monotonic() + POLL_SECONDS
                while _pending is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    _cond.wait(remaining)

                command, _pending = _pending, None
            finally:
                _waiting_polls -= 1
                _seen()

        body = b""
        if command:
            body = json.dumps({"id": command[0], "volume": command[1]}).encode()
        self._reply(200, body)

    def do_POST(self):
        if not self._from_userscript():
            return self._reply(404)

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._reply(400)

        with _cond:
            if self.path == "/ytmusic/volume":
                _seen()
                _results[data.get("id")] = data.get("level")
            elif self.path == "/ytmusic/state":
                _seen(bool(data.get("playing")))
            else:
                return self._reply(404)
            _cond.notify_all()

        self._reply(200)


def start():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), _Handler)
    except OSError as e:
        print("YouTube Music bridge not started:", e)
        return None

    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
