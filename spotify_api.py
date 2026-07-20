import requests

def get_album_art_url(song_title, artist):
    try:
        r = requests.get(
            "https://api.deezer.com/search",
            params={
                "q": f"{artist} {song_title}",
                "limit": 1
            },
            timeout=3
        )
        data = r.json()
        results = data.get("data", [])

        if results:
            return results[0]["album"]["cover_xl"]

    except Exception as e:
        print("Deezer error:", e)

    return None