import json
import requests
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
from dateutil import parser as dateparser
from os import makedirs as mkdir

header = {"Accept": "application/json", "User-Agent": "databass/0.3 (https://github.com/chunned/databass)"}

# Load environment variables
load_dotenv()
DISCOGS_KEY = os.getenv("DISCOGS_KEY")
DISCOGS_SECRET = os.getenv("DISCOGS_SECRET")

if not DISCOGS_KEY or not DISCOGS_SECRET:
    print("Error: Discogs API keys not found. Please set DISCOGS_KEY and DISCOGS_SECRET in your environment.")
    exit(1)


def pick_release(release, artist):
    # Accepts search parameters and returns a list of matching releases, which the user must select from

    url = "https://musicbrainz.org/ws/2/release/"
    params = {
        "query": f'artist:"{artist}" AND release:"{release}"',
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
            # TODO: make an attempt to grab original release date
            # try using Discogs master release: https://www.discogs.com/developers#page:database,header:database-master-release
            print(f'Attempting to extract year from search data: {release["date"]}')
            raw_date = release["date"]
            try:
                date = dateparser.parse(raw_date, fuzzy=True).year
                print(f'Extracted year: {date}')
            except Exception as e:
                print(f'ERROR: {e}')
                date = "?"
        except KeyError:
            date = "?"

        try:
            release_format = release["media"][0]["format"]
        except KeyError:
            release_format = "unknown"

        rel = {
            "release": {
                "name": release["title"],
                "mbid": release['id']
            },
            "artist": {
                "name": release["artist-credit"][0]["name"],
                "mbid": release["artist-credit"][0]["artist"]["id"],
            },
            "label": label,
            "date": date,
            "format": release_format,
            "track-count": release["track-count"],
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
    image = get_image(mbid, 'release', [title, artist])

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
    local_timezone = pytz.timezone(os.getenv('TIMEZONE'))
    listen_date = datetime.now(local_timezone).strftime("%Y-%m-%d")

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
        "image": image
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


def get_image(mbid, item_type, discog_release):
    # Grab cover image for a given release by MusicBrainzID
    try:
        # Try to grab cover image from CoverArtArchive
        print(f'INFO: Attempting to grab cover image from CoverArtArchive: {mbid}')
        response = requests.get(f'https://coverartarchive.org/{item_type}/{mbid}', headers=header)
        response = response.json()
        print(response)
        image = response['images'][0]['image']
    except requests.exceptions.JSONDecodeError:
        # Fallback to Discogs
        print(f'ERROR: No cover image found on CoverArtArchive. Trying Discogs')
        image = discogs_get_image(discog_release, item_type)
        print(f'INFO: Discogs returned {image}')
        if image is None:
            # If not found on Discogs, use a static 'not-found' template image
            # TODO: store this locally
            image = 'https://static.vecteezy.com/system/resources/thumbnails/005/720/408/small_2x/crossed-image-icon-picture-not-available-delete-picture-symbol-free-vector.jpg'
    return image


def get_artist_data(mbid):
    # Query basic metadata about an artist by its MusicBrainz ID
    url = f"https://musicbrainz.org/ws/2/artist/{mbid}"
    response = requests.get(url, headers=header)
    result = response.json()

    artist = {"mbid": mbid, "name": result["name"], "country": result["country"],
              "begin_date": result["life-span"]["begin"], "end_date": result["life-span"]["end"],
              "image": get_image(mbid, 'artist', result["name"]), "type": None}

    if result["type"] == "Person":
        artist["type"] = "person"
    elif result["type"] == "Group":
        artist["type"] = "group"

    return artist


def get_label_data(mbid):
    # Query basic metadata about a label by its MusicBrainz ID
    url = f"https://musicbrainz.org/ws/2/label/{mbid}"
    print(f'INFO: Querying MusicBrainz API: {url}')
    response = requests.get(url, headers=header)
    result = response.json()
    print(f'INFO: Response from MusicBrainz API: {response}')
    image = get_image(mbid, 'label', result["name"])

    label = {
        "mbid": mbid,
        "name": result["name"],
        "country": result["country"],
        "type": result["type"],
        "begin_date": result["life-span"]["begin"],
        "end_date": result["life-span"]["end"],
        "image": image
    }
    print(f'INFO: Label data: {label}')
    return label


# Discogs API functions
def discogs_get_image(name, item_type):
    # Used by get_image to query Discogs API
    header["Authorization"] = f"Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}"
    url = 'https://api.discogs.com/'

    print(f'INFO: Querying Discogs API: {name}, {item_type}')
    if item_type == 'release':
        search_endpoint = f"/database/search?q={name[1]}&type=release&release_title={name[0]}"
    else:
        search_endpoint = f"/database/search?q={name}&type={item_type}"
    print(f'INFO: Search endpoint: {search_endpoint}')

    response = requests.get(url+search_endpoint, headers=header)
    result = response.json()
    print(f'INFO: Discogs API returned:\n{result}')
    image = None
    if not result:
        return image
    try:
        # Check for Discogs API error
        if result['message'] == "Discogs is unavailable right now.":
            print("ERROR: Discogs API currently unavailable")
            return image
    except KeyError:
        # No error message, continue
        pass
    for item in result["results"]:
        if item_type == 'release':
            image = item["cover_image"]
            break
        else:
            if item["title"].lower() == name.lower():
                image = result["results"][0]["cover_image"]
                break
    print(f'INFO: Image: {image}')
    return image


def download_image(item_type, item_id, img_url):
    print(f'INFO: URL - {img_url}')
    base_path = "./static/img"
    item_type_map = {
        'release': 'release',
        'artist': 'artist',
        'label': 'label'
    }
    try:
        # attempt to download the image
        image_type = get_image_type_from_url(img_url)
        print(f'INFO: Image type: {image_type}')
        if image_type:
            subdir = item_type_map[item_type]
            filename = str(item_id) + image_type
            path = base_path + '/' + subdir + '/' + filename
            print(f'INFO: Image will be saved in {path}')
            response = requests.get(img_url, headers=header)
            with open(path, 'wb') as img_file:
                img_file.write(response.content)
            return path
        else:
            return ''
    except KeyError:
        print('ERROR: Invalid item_type: ', item_type)
    except FileNotFoundError:
        # directory does not exist, create it
        print('INFO: Creating directories...')
        mkdir(f"{base_path}/release", exist_ok=True)
        mkdir(f"{base_path}/artist", exist_ok=True)
        mkdir(f"{base_path}/label", exist_ok=True)
        print('INFO: Directories created. Calling function again.')
        # call this function again
        download_image(item_type, item_id, img_url)


def get_image_type_from_url(url):
    # Take a URL (string) and return the image type
    try:
        if url.endswith('.jpg'):
            return '.jpg'
        elif url.endswith('.jpeg'):
            return '.jpeg'
        elif url.endswith('.png'):
            return '.png'
        else:
            raise KeyError('ERROR: Invalid image type')
    except KeyError as e:
        print(f'{e}: {url}')
