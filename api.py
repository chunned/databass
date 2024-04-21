import json

import requests
from datetime import datetime
import os

header = {"Accept": "application/json", "User-Agent": "databass/0.2 (https://github.com/chunned/databass)"}

DISCOGS_KEY = os.getenv("DISCOGS_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_SECRET")


def pick_release(release, artist, rating, year, genre):
    url = "https://musicbrainz.org/ws/2/release/"
    params = {
        "query": f'artist:"{artist}" AND release:"{release}"',
        "limit": 10,
        "fmt": "json",
    }

    response = requests.get(url, params=params, headers=header)
    result = response.json()

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

        try:
            release_format = release["media"][0]["format"]
        except KeyError:
            release_format = "unknown"

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
            "format": release_format,
            "track-count": release["track-count"],
            "rating": rating,
            "release_date": year,
            "genre": genre
        }
        result_data.append(rel)

    return result_data


def get_release_data(mbid, year, genre, rating):
    # mid = musicbrainz ID
    url = f"https://musicbrainz.org/ws/2/release/{mbid}?inc=recordings+tags+artist-credits"
    response = requests.get(url, headers=header)
    result = response.json()

    artist = result['artist-credit'][0]['name']
    title = result['title']
    art = get_art(mbid, 'release', [title, artist])

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


def get_art(mbid, item_type, discog_release):
    try:
        # Try to grab cover art
        response = requests.get(f'https://coverartarchive.org/{item_type}/{mbid}', headers=header)
        response = response.json()
        art = response['images'][0]['image']
    except requests.exceptions.JSONDecodeError:
        # fallback to Discogs
        art =  discogs_get_image(discog_release, item_type)
        if art is None:
            art = 'https://static.vecteezy.com/system/resources/thumbnails/005/720/408/small_2x/crossed-image-icon-picture-not-available-delete-picture-symbol-free-vector.jpg'
    return art


def get_artist_data(mbid):
    url = f"https://musicbrainz.org/ws/2/artist/{mbid}"
    response = requests.get(url, headers=header)
    result = response.json()

    artist = {"mbid": mbid, "name": result["name"], "country": result["country"],
              "begin_date": result["life-span"]["begin"], "end_date": result["life-span"]["end"],
              "image": get_art(mbid, 'artist', result["name"]), "type": None}

    if result["type"] == "Person":
        artist["type"] = "person"
    elif result["type"] == "Group":
        artist["type"] = "group"

    return artist


def get_label_data(mbid):
    url = f"https://musicbrainz.org/ws/2/label/{mbid}"
    response = requests.get(url, headers=header)
    result = response.json()

    image = get_art(mbid, 'label', result["name"])

    label = {
        "mbid": mbid,
        "name": result["name"],
        "country": result["country"],
        "type": result["type"],
        "begin_date": result["life-span"]["begin"],
        "end_date": result["life-span"]["end"],
        "image": image
    }
    return label


# Discogs API functions
def discogs_get_image(name, item_type):
    header["Authorization"] = f"Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}"
    url = 'https://api.discogs.com/'

    if item_type == 'release':
        search_endpoint = f"/database/search?q={name[1]}&type=release&release_title={name[0]}"
    else:
        search_endpoint = f"/database/search?q={name}&type={item_type}"

    response = requests.get(url+search_endpoint, headers=header)
    result = response.json()
    image = None
    for item in result["results"]:
        if item_type == 'release':
            image = item["cover_image"]
            break
        else:
            if item["title"].lower() == name.lower():
                image = result["results"][0]["cover_image"]
                break
    return image

