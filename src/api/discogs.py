from dotenv import load_dotenv
from os import getenv
import requests
import re

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
            if resp.status_code == 200:
                return resp.json()
            else:
                raise requests.exceptions.RequestException(f'Status code != 200: {resp}')

    @staticmethod
    def get_item_image_url(endpoint):
        # Receives an API endpoint with query; extracts the first square image found
        response = Discogs.request(endpoint)
        results = response["results"]
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
                    continue
                else:
                    return image_url
            except Exception as e:
                raise e

    @staticmethod
    def get_release_image_url(name: str, artist: str):
        endpoint = f"/database/search?q={artist}&type=release&release_title={name}"
        return Discogs.get_item_image_url(endpoint)

    @staticmethod
    def get_artist_image_url(name: str):
        endpoint = f"/database/search?q={name}&type=artist"
        return Discogs.get_item_image_url(endpoint)

    @staticmethod
    def get_label_image_url(name: str):
        endpoint = f"/database/search?q={name}&type=label"
        return Discogs.get_item_image_url(endpoint)

