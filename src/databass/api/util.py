import datetime
import glob
import requests
from os import getenv
from dotenv import load_dotenv
import pathlib

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
        img = img_type = img_url = None
        base_path = "./databass/static/img"
        subdir = item_type
        try:
            # Create image subdirectory
            pathlib.Path(f"{base_path}/{subdir}").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f'Encountered exception while creating directory: {e}')

        if item_type not in ['release', 'artist', 'label']:
            raise Exception(f'Unexpected item_type: {item_type}')

        from .discogs import Discogs

        if mbid is not None and item_type == 'release':
            print(f'Item is a release and MBID is populated; attempting to fetch image from CoverArtArchive: {mbid}')
            from .musicbrainz import MusicBrainz
            try:
                img = MusicBrainz.get_image(mbid)
                if img is not None:
                    print('CoverArtArchive image found')
                    # CAA returns the raw image data
                    img_type = Util.get_image_type_from_bytes(img)
                else:
                    raise ValueError('No image returned by CoverArtArchive, or an error was encountered when fetching the image.')
            except Exception:
                print('Image not found on CAA, checking Discogs')
                try:
                    img_url = Discogs.get_release_image_url(
                        name=release_name,
                        artist=artist_name
                    )
                except Exception as e:
                    print(f'Got an exception from Discogs: {e}')
        else:
            print(f'Attempting to fetch {item_type} image from Discogs')
            if item_type == 'artist':
                img_url = Discogs.get_artist_image_url(name=artist_name)
            elif item_type == 'label':
                img_url = Discogs.get_label_image_url(name=label_name)
        response = ''
        if img_url is not None and img_url is not False:
            print(f'Discogs image URL: {img_url}')
            response = requests.get(img_url, headers={
                "Accept": "application/json",
                "User-Agent": f"databass/{VERSION} (https://github.com/chunned/databass)"
            })
            img = response.content
            img_type = Util.get_image_type_from_bytes(img)

        if img is not None and img_type is not None:
            file_name = str(item_id) + img_type
            file_path = base_path + '/' + subdir + '/' + file_name
            with open(file_path, 'wb') as img_file:
                img_file.write(img)
            print(f'Image saved to {file_path}')
            return file_path.replace('databass/', '')
        else:
            print('img or img_type was blank; requires manual debug')
            print(f'Discogs response: {response}')

    @staticmethod
    def img_exists(item_id, item_type):
        result = glob.glob(f'databass/static/img/{item_type}/{item_id}.*')
        if result:
            url = '/' + result[0].replace('databass/', "")
            return url
        else:
            return result