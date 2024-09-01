import datetime
import requests
from os import mkdir, getenv
from dotenv import load_dotenv

load_dotenv()
VERSION = getenv('VERSION')


# Collection of generic utility functions used by other parts of the app
class Util:
    @staticmethod
    def to_date(begin_or_end: str, date_str: str):
        # Receives a string representing an artist or label's begin_date or end_date
        # Converts to datetime object
        date = None
        if not date_str:
            if begin_or_end == 'begin':
                date = datetime.datetime(year=1, month=1, day=1)
            elif begin_or_end == 'end':
                date = datetime.datetime(year=9999, month=12, day=31)
        elif len(date_str) == 4:
            date = datetime.datetime.strptime(date_str, "%Y")
        elif len(date_str) == 7:
            date = datetime.datetime.strptime(date_str, "%Y-%m")
        elif len(date_str) == 10:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d")

        if date is not None:
            return date.date()
        else:
            raise ValueError(f"Unexpected date string format: {date_str}")

    @staticmethod
    def today():
        # Return current day as a string
        return datetime.datetime.today().strftime('%Y-%m-%d')

    @staticmethod
    def get_page_range(per_page, current_page):
        # Calculates the page range for pagination
        start = (current_page - 1) * per_page
        end = start + per_page
        return start, end

    @staticmethod
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
            raise f'{e}: {url}'

    @staticmethod
    def get_image_type_from_bytes(bytestr):
        try:
            if bytestr.startswith(b'\xff\xd8\xff'):
                return '.jpg'
            elif bytestr.startswith(b'\x89PNG\r\n\x1a\n'):
                return '.png'
            elif bytestr.startswith(b'GIF87a') or bytestr.startswith(b'GIF89a'):
                return '.gif'
        except Exception as e:
            raise e

    @staticmethod
    def get_image(
            item_type: str,
            item_id: str | int,
            mbid: str = None,
            release_name: str = None,
            artist_name: str = None,
            label_name: str = None
    ):
        img = img_type = None
        base_path = "./static/img"
        subdir = item_type
        try:
            # Create image subdirectory
            mkdir(f"{base_path}/{subdir}")
        except FileExistsError:
            pass  # Directory already exists; continue

        if item_type not in ['release', 'artist', 'label']:
            raise Exception(f'Unexpected item_type: {item_type}')
        if mbid is not None and item_type == 'release':
            # Item is a release and MBID is populated; attempting to fetch image from CoverArtArchive
            from .musicbrainz import MusicBrainz
            img = MusicBrainz.get_image(mbid)
            if img is not None:
                # CoverArtArchive image found
                # CAA returns the raw image data
                img_type = Util.get_image_type_from_bytes(img)
        else:
            # Attempting to fetch image from Discogs
            from .discogs import Discogs
            img_url = None
            if item_type == 'release':
                img_url = Discogs.get_release_image_url(name=release_name,
                                                        artist=artist_name)
            elif item_type == 'artist':
                img_url = Discogs.get_artist_image_url(name=artist_name)
            elif item_type == 'label':
                img_url = Discogs.get_label_image_url(name=label_name)
            if img_url is not None:
                response = requests.get(img_url, headers={
                    "Accept": "application/json",
                    "User-Agent": f"databass/{VERSION} (https://github.com/chunned/databass)"
                })
                img = response.content

        if img is not None and img_type is not None:
            file_name = str(item_id) + img_type
            file_path = base_path + '/' + subdir + '/' + file_name
            with open(file_path, 'wb') as img_file:
                img_file.write(img)
            return file_path
        else:
            raise Exception('img or img_type was blank; requires manual debug')
