from dotenv import load_dotenv
from os import getenv
import requests
import re
import urllib.parse
import time

load_dotenv()
DISCOGS_KEY = getenv("DISCOGS_KEY")
DISCOGS_SECRET = getenv("DISCOGS_SECRET")
VERSION = getenv("VERSION")


class Discogs:
    url = 'https://api.discogs.com'
    headers = {
        "User-Agent": f"Databass/{VERSION} +https://github.com/chunned/databass",
        "Authorization": f"Discogs key={DISCOGS_KEY}, secret={DISCOGS_SECRET}"
    }
    remaining_requests = None

    @classmethod
    def update_rate_limit(cls, response: requests.Response):
        limit = response.headers.get("x-discogs-ratelimit-remaining")
        cls.remaining_requests = int(limit)
        print('Remaining: ', cls.remaining_requests)

    @classmethod
    def is_throttled(cls):
        if cls.remaining_requests is not None and cls.remaining_requests <= 2:
            return True
        else:
            return False

    @staticmethod
    def request(endpoint: str):
        # Sends request to an endpoint then updates rate limit count
        # Returns json if response code is 200
        if not Discogs.is_throttled():
            resp = requests.get(Discogs.url+endpoint, headers=Discogs.headers)
            Discogs.update_rate_limit(resp)
            time.sleep(1)
            if resp.status_code == 200:
                return resp.json()
            else:
                raise requests.exceptions.RequestException(f'Status code != 200: {resp}')
        else:
            print('ERROR: Discogs rate limit exceeded. Please wait.')

    @staticmethod
    def get_item_id(name: str,
                      item_type: str,
                      artist: str = None):
        print(f"Getting ID for {item_type}: {name}")
        if item_type == 'release':
            query_params = {
                "q": artist,
                "type": "release",
                "release_title": name
            }
        else:
            query_params = {
                "q": name,
                "type": item_type
            }
        encoded_params = urllib.parse.urlencode(query_params)
        endpoint = f"/database/search?{encoded_params}"
        print(f'Search endpoint: {endpoint}')

        res = Discogs.request(endpoint)
        try:
            for result in res["results"]:
                if "Blu-ray" not in result["format"]:
                    item_id = result["id"]
                    break
                else:
                    pass    # Skip bluray releases
        except IndexError:
            return False
        if item_id:
            print(f'ID for {item_type} {name}: {item_id}')
            return item_id
        else:
            return False

    @staticmethod
    def get_item_image_url(endpoint):
        # Receives an API endpoint with query; extracts the first square image found
        response = Discogs.request(endpoint)
        try:
           results = response["results"]
        except TypeError:
            return None
        for item in results:
            image_url = item["cover_image"]
            try:
                # Attempt to determine image dimensions from the URL
                # Should contain a string like /h:500/w:500/ to denote the height and width
                # Below regex first extracts that entire substring; the next extract the height and width themselves

                # IN: https://........../h:250/w:500/......  OUT: "/h:250/w:500"
                dimensions = re.findall(r'/h:\d+/w:\d+/', image_url)[0]
                # IN: "/h:250/w:500"                         OUT: 250
                height = int(re.sub(r'/h:(\d+)/.*', r'\1', dimensions))
                # IN: "/h:250/w:500"                         OUT: 500
                width = int(re.sub(r'.*/w:(\d+)/.*', r'\1', dimensions))

                # Make sure image is square; if not, try next result
                if not height == width:
                    pass
                else:
                    return image_url
            except Exception as e:
                pass
        print('INFO: No square images found.')

    @staticmethod
    def find_image(search_results: dict):
        """
        INPUT: results from a Discogs API query
        OUTPUT: first square image found in search results
        """
        try:
            print(f'{len(search_results["images"])} candidates found')
            for image in search_results["images"]:
                image_url = image["uri"]
                try:
                    height = image["height"]
                    width = image["width"]
                    # Make sure image is square; if not, try next result
                    if not height == width:
                        print(f'Non-square image: H:{height}/W:{width} | {image_url}')
                        pass
                    else:
                        print(f'Square image found: {image_url}')
                        return image_url
                except Exception as e:
                    raise e
            print('No square images found. Returning first image result')
            return search_results["images"][0]["uri"]
        except KeyError:
            print('No images found in search results.')
            return False

    @staticmethod
    def get_release_image_url(name: str, artist: str):
        release_id = Discogs.get_item_id(
            name=name,
            artist=artist,
            item_type='release'
        )
        if release_id:
            print(f'Got release ID. Checking for images...')
            endpoint = f"/releases/{release_id}"
            res = Discogs.request(endpoint)
            return Discogs.find_image(res)
        else:
            print('No search results found.')
            return None

    @staticmethod
    def get_artist_image_url(name: str):
        artist_id = Discogs.get_item_id(name=name, item_type='artist')
        if artist_id:
            print(f'Got artist ID. Checking for images.')
            endpoint = f"/artists/{artist_id}"
            res = Discogs.request(endpoint)
            return Discogs.find_image(res)
        else:
            print('No search results found.')
            return None


    @staticmethod
    def get_label_image_url(name: str):
        label_id = Discogs.get_item_id(name=name, item_type='label')
        if label_id:
            print(f'Got label ID. Checking for images.')
            endpoint = f"/labels/{label_id}"
            res = Discogs.request(endpoint)
            return Discogs.find_image(res)
        else:
            print('No search results found.')
            return None
