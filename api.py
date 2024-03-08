import json
import requests
from datetime import datetime

header = {"Accept": "application/json", "User-Agent": "Databass/0.1 (https://github.com/hcnolan)"}


def show_release_details(rel):
    # Print title and artist
    artist = rel["artist-credit"][0]["name"]
    title = rel["title"]
    w = 50
    print(f'ARTIST: {artist}')
    print(f'TITLE:  {title}')

    # Print date, if it exists
    if 'date' in rel:
        date = rel["date"] + " (" + rel["status"] + ")"
        print(f'DATE:   {date}')
    else:
        print('DATE: unknown')

    # Show release type
    media_type = rel["media"][0]["format"]
    tracks = rel["track-count"]
    print(f'TYPE:   {media_type}')
    # Print track count
    print(f'TRACKS: {tracks}')

    # Print URL
    url = "https://musicbrainz.org/release/" + rel['id']
    print(f"URL:    {url}")


def pick_release():
    release = input("Release title: ")
    artist = input("Release artist: ")
    url = "https://musicbrainz.org/ws/2/release/"
    params = {
        "query": f'artist:"{artist}" AND release:"{release}"',
        "limit": 5,
        "fmt": "json",
    }

    response = requests.get(url, params=params, headers=header)
    result = response.json()

    # iterate through release results to find the correct one
    for (i, release) in enumerate(result['releases']):
        print(f'MATCH #{i + 1}:')
        show_release_details(release)
        check = ' '
        print()
        while check.lower() not in "yn":
            check = input("Is this the correct release? (y/n): ")
            if check.lower() not in "yn":
                print(f"{check} is not a valid choice. Please enter Y or N.")
        if check.lower() == 'y':
            release_id = release['id']
            artist_name = release["artist-credit"][0]["name"]
            artist_id = release["artist-credit"][0]["artist"]["id"]
            artist = {"mbid": artist_id, "name": artist_name}
            try:
                label = {
                    "mbid": release['label-info'][0]['label']['id'],
                    "name": release['label-info'][0]['label']['name']
                }
            except KeyError:
                label = None
            return release_id, artist, label
    # TODO: edge cases where match is not found; or more than 5 results exist


def get_release_data(mbid, artist_id, label_id):
    # mid = musicbrainz ID
    url = f"https://musicbrainz.org/ws/2/release/{mbid}?inc=recordings+tags"
    response = requests.get(url, headers=header)
    result = response.json()

    # pretty = json.dumps(result, indent=4)
    # print(pretty)

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
    genre = input("Release genre: ")
    # Get release length (in ms)
    length = 0
    tracks = result['media'][0]['tracks']
    for track in tracks:
        length += track['length']
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
        "genre": genre
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



