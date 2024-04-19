import json
import requests
from datetime import datetime

header = {"Accept": "application/json", "User-Agent": "databass/0.2 (https://github.com/chunned/databass)"}


def pick_release(release, artist):
    url = "https://musicbrainz.org/ws/2/release/"
    params = {
        "query": f'artist:"{artist}" AND release:"{release}"',
        "limit": 10,
        "fmt": "json",
    }

    response = requests.get(url, params=params, headers=header)
    result = response.json()

    print(json.dumps(result, indent=2))

    result_data = []
    for (i, release) in enumerate(result['releases']):
        try:
            label = {
                "mbid": release['label-info'][0]['label']['id'],
                "name": release['label-info'][0]['label']['name']
            }
        except KeyError:
            label = {"name": ""}

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
                "id": release["artist-credit"][0]["artist"]["id"],
            },
            "label": label,
            "date": date,
            "format": release["media"][0]["format"],
            "track-count": release["track-count"]
        }
        result_data.append(rel)

    return result_data


def get_release_data(mbid, artist_id, label_id):
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
    release_date = None
    while not release_date:
        try:
            release_date = input('Enter the release year: ')
            if len(release_date) != 4:
                raise ValueError
        except ValueError:
            print('Please enter a 4 digit year.')
            release_date = None
    track_count = result['media'][0]['track-count']
    try:
        area = result['release-events'][0]['area']['name']
    except TypeError:
        area = None
    except KeyError:
        area = None
    genre = input("Release genre: ")
    # Get release length (in ms)
    length = 0
    tracks = result['media'][0]['tracks']
    try:
        for track in tracks:
            length += track['length']
    except TypeError:
        length = 0
    listen_date = datetime.now().strftime("%Y-%m-%d")
    rating = 0
    try:
        rating = int(input("Rating (0-100): "))
        if rating < 0 or rating > 100:
            raise ValueError
    except ValueError as e:
        print("Invalid rating")

    data = {
        "mbid": mbid,
        "title": title,
        "release_date": release_date,
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



