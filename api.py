import json
import requests
from datetime import datetime

header = {"Accept": "application/json", "User-Agent": "databass/0.2 (https://github.com/chunned/databass)"}


def pick_release(release, artist, rating, year, genre):
    url = "https://musicbrainz.org/ws/2/release/"
    params = {
        "query": f'artist:"{artist}" AND release:"{release}"',
        "limit": 10,
        "fmt": "json",
    }

    response = requests.get(url, params=params, headers=header)
    result = response.json()

    #print(json.dumps(result, indent=2))

    result_data = []
    for (i, release) in enumerate(result['releases']):
        try:
            label = {
                "mbid": release['label-info'][0]['label']['id'],
                "name": release['label-info'][0]['label']['name']
            }
        except KeyError:
            label = {"name": "", "mbid": ""}

        try:
            date = release["date"]
        except KeyError:
            date = "?"

        rel = {
            "release": {
                "name": release["title"],
                "id": release['id']
            },
            "artist": {
                "name": release["artist-credit"][0]["name"],
                "mbid": release["artist-credit"][0]["artist"]["id"],
            },
            "label": label,
            "date": date,
            "format": release["media"][0]["format"],
            "track-count": release["track-count"],
            "rating": rating,
            "release_date": year,
            "genre": genre
        }
        result_data.append(rel)

    return result_data


def get_release_data(mbid, year, genre, rating):
    # mid = musicbrainz ID
    url = f"https://musicbrainz.org/ws/2/release/{mbid}?inc=recordings+tags"
    response = requests.get(url, headers=header)
    result = response.json()

    # pretty = json.dumps(result, indent=4)
    # print(pretty)
    try:
        # Try to grab cover art
        response = requests.get(f'https://coverartarchive.org/release/{mbid}', headers=header)
        response = response.json()
        art = response['images'][0]['image']
    except requests.exceptions.JSONDecodeError:
        art = 'https://static.vecteezy.com/system/resources/thumbnails/005/720/408/small_2x/crossed-image-icon-picture-not-available-delete-picture-symbol-free-vector.jpg'

    title = result['title']

    track_count = result['media'][0]['track-count']
    try:
        area = result['release-events'][0]['area']['name']
    except TypeError:
        area = None
    except KeyError:
        area = None
    # Get release length (in ms)
    length = 0
    tracks = result['media'][0]['tracks']
    try:
        for track in tracks:
            length += track['length']
    except TypeError:
        length = 0
    listen_date = datetime.now().strftime("%Y-%m-%d")

    data = {
        "mbid": mbid,
        "title": title,
        "release_date": year,
        "runtime": length,
        "rating": rating,
        "listen_date": listen_date,
        "track_count": track_count,
        "country": area,
        "genre": genre,
        "art": art
    }
    return data


def get_artist_mbid(artist_name):
    url = f"https://musicbrainz.org/ws/2/artist/?query=artist:{artist_name}"
    response = requests.get(url, headers=header)
    result = response.json()

    mbid = None
    try:
        mbid = result['artists'][0]['id']
    except KeyError:
        pass
    return mbid


def get_label_mbid(label_name):
    url = f"https://musicbrainz.org/ws/2/label/?query={label_name}"
    response = requests.get(url, headers=header)
    result = response.json()

    mbid = None
    try:
        mbid = result['labels'][0]['id']
    except KeyError:
        pass
    return mbid



