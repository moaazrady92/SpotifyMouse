from media_session import get_now_playing


def get_current_song():
    # Whatever is playing: Spotify, YouTube Music in a browser, any media app
    try:
        return get_now_playing()
    except Exception as e:
        print("Now playing error:", e)
        return None
