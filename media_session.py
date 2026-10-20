import asyncio
import threading

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus,
)
from winrt.windows.storage.streams import Buffer, InputStreamOptions

# Windows' media session API sees every player that shows up in the
# volume flyout: Spotify, browsers (YouTube Music, etc.), media apps.
# Controlling the session directly works no matter which app Windows
# would otherwise send the media keys to.

_manager = None
_manager_lock = threading.Lock()

# The player we last controlled, so pressing play again resumes the
# same thing that was just paused
_last_source = None


async def _get_manager():
    global _manager
    with _manager_lock:
        manager = _manager
    if manager is None:
        manager = await SessionManager.request_async()
        with _manager_lock:
            _manager = manager
    return manager


def _is_playing(session):
    status = session.get_playback_info().playback_status
    return status == PlaybackStatus.PLAYING


def _find(sessions, source):
    for session in sessions:
        if source and session.source_app_user_model_id == source:
            return session
    return None


async def _pick_session(source=None):
    manager = await _get_manager()
    sessions = list(manager.get_sessions())

    if not sessions:
        return None

    if source:
        return _find(sessions, source)

    current = manager.get_current_session()
    current_source = current.source_app_user_model_id if current else None

    # Something playing wins; among several, prefer the one we last
    # controlled, then the one Windows considers current
    playing = [s for s in sessions if _is_playing(s)]
    candidates = playing or sessions

    return (
        _find(candidates, _last_source)
        or _find(candidates, current_source)
        or candidates[0]
    )


async def _control(action):
    # Returns None if there's no player at all, else whether it accepted
    global _last_source

    session = await _pick_session()
    if not session:
        return None

    _last_source = session.source_app_user_model_id
    return bool(await getattr(session, action)())


def has_session():
    return asyncio.run(_pick_session()) is not None


def get_target_source():
    # The player that play/pause/skip would control right now
    session = asyncio.run(_pick_session())
    return session.source_app_user_model_id if session else None


def toggle_play_pause():
    return asyncio.run(_control("try_toggle_play_pause_async"))


def skip_next():
    return asyncio.run(_control("try_skip_next_async"))


def skip_previous():
    return asyncio.run(_control("try_skip_previous_async"))


async def _now_playing():
    session = await _pick_session()

    if not session or not _is_playing(session):
        return None

    props = await session.try_get_media_properties_async()

    if not props or not props.title:
        return None

    return {
        "title": props.title,
        "artist": props.artist or props.album_artist or "",
        "source": session.source_app_user_model_id,
    }


def get_now_playing():
    return asyncio.run(_now_playing())


async def _thumbnail(source):
    session = await _pick_session(source)
    if not session:
        return b""

    props = await session.try_get_media_properties_async()
    if not props or not props.thumbnail:
        return b""

    stream = await props.thumbnail.open_read_async()
    buffer = Buffer(stream.size)
    await stream.read_async(buffer, stream.size, InputStreamOptions.READ_AHEAD)
    return bytes(buffer)


def get_thumbnail(source):
    return asyncio.run(_thumbnail(source))
