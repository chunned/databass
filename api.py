import json
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

header = {"Accept": "application/json", "User-Agent": "databass/0.2 (https://github.com/chunned/databass)"}

# Load environment variables
load_dotenv()
DISCOGS_KEY = os.getenv("DISCOGS_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_SECRET")

if not DISCOGS_KEY or not DISCOGS_SECRET:
    print("Error: Discogs API keys not found. Please set DISCOGS_KEY and DISCOGS_SECRET in your environment.")
    exit(1)


def pick_release(release, artist, rating, year, genre, tags):
    # Accepts search parameters and returns a list of matching releases, which the user must select from

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
            "genre": genre,
            "tags": tags
        }
        result_data.append(rel)

    return result_data


def get_release_data(mbid, year, genre, rating):
    # Grabs data for a specific release by its MusicBrainz ID
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
    # TODO: merge with get_label_mbid
    # Grab the MusicBrainz ID for a given artist name.
    # Note that this is best-effort and no checking on the name is performed
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
    # TODO: merge with get_artist_mbid
    # Grab the MusicBrainz ID for a given label name.
    # Note that this is best-effort and no checking on the name is performed
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
    # Grab cover art for a given release by MusicBrainzID
    try:
        # Try to grab cover art from CoverArtArchive
        response = requests.get(f'https://coverartarchive.org/{item_type}/{mbid}', headers=header)
        response = response.json()
        art = response['images'][0]['image']
    except requests.exceptions.JSONDecodeError:
        # Fallback to Discogs
        art = discogs_get_image(discog_release, item_type)
        if art is None:
            # If not found on Discogs, use a static 'not-found' template image
            # TODO: store this locally
            art = 'https://static.vecteezy.com/system/resources/thumbnails/005/720/408/small_2x/crossed-image-icon-picture-not-available-delete-picture-symbol-free-vector.jpg'
    return art


def get_artist_data(mbid):
    # Query basic metadata about an artist by its MusicBrainz ID
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
    # Query basic metadata about a label by its MusicBrainz ID
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
    # Used by get_art to query Discogs API for cover art images
    header["Authorization"] = f"Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}"
    url = 'https://api.discogs.com/'

    if item_type == 'release':
        search_endpoint = f"/database/search?q={name[1]}&type=release&release_title={name[0]}"
    else:
        search_endpoint = f"/database/search?q={name}&type={item_type}"

    response = requests.get(url+search_endpoint, headers=header)
    result = response.json()
    image = None
    if not result:
        return image
    for item in result["results"]:
        if item_type == 'release':
            image = item["cover_image"]
            break
        else:
            if item["title"].lower() == name.lower():
                image = result["results"][0]["cover_image"]
                break
    return image

