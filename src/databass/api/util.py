import datetime
import glob
import requests
from os import getenv
from dotenv import load_dotenv
import pathlib
import signal

load_dotenv()
VERSION = getenv('VERSION')

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Request timed out")




# Collection of generic utility functions used by other parts of the app
class Util:
    @staticmethod
    def to_date(begin_or_end: str | None, date_str: str | None) -> datetime.date:
        """
        Takes a string representation of a date and returns a datetime object.
        :param begin_or_end: String representing whether this is the artist/label's start or end date. Has no purpose unless date_str is None, so it may be None
        :param date_str: String representing the date, or None if no string was found in API search results
        :return: Datetime object representing the input date_str. If date_str was None, then returns the 'max' or 'min' date depending on begin_or_end
        """
        date = None
        if not date_str:
            if not begin_or_end:
                raise ValueError("Must be used with either begin_or_end or date_str, or both")
            # No date in search results, return max/min date
            elif begin_or_end == 'begin':
                date = datetime.datetime(year=1, month=1, day=1)
            elif begin_or_end == 'end':
                date = datetime.datetime(year=9999, month=12, day=31)

        # Date found in search results
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
    def get_page_range(per_page: int, current_page: int) -> (int, int):
        """
        Calculates the range of elements to slice from a list to use for pagination
        :param per_page: Amount of results per page
        :param current_page: Page number
        :return: Tuple representing the start and end index to slice
        """
        start = (current_page - 1) * per_page
        end = start + per_page
        return start, end

    @staticmethod
    def get_image_type_from_url(url: str) -> str:
        """
        Determine image file extension given its URL; by extension acts as an image format filter
        :param url: String representation of the URL
        :return: String representation of the image file extension
        """
        try:
            if url.endswith('.jpg'):
                return '.jpg'
            elif url.endswith('.jpeg'):
                return '.jpeg'
            elif url.endswith('.png'):
                return '.png'
            else:
                raise ValueError(f'ERROR: Invalid image type. URL: {url}')
        except ValueError as e:
            raise e

    @staticmethod
    def get_image_type_from_bytes(bytestr: bytes) -> str:
        """
        Determine image file extension from bytes; by extension acts as an image format filter
        :param bytestr: Byte representation of an image file
        :return: String representation of the image file extension
        """
        try:
            if bytestr.startswith(b'\xff\xd8\xff'):
                return '.jpg'
            elif bytestr.startswith(b'\x89PNG\r\n\x1a\n'):
                return '.png'
            else:
                raise ValueError("Either image file is invalid or is not a supported filetype - supported types are jpg and png.")
        except ValueError as e:
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
        # TODO: refactor
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
                # Number of seconds to wait before raising a TimeoutException
                timeout_duration = 5
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout_duration)

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
    def img_exists(
            item_id: int,
            item_type: str
    ) -> str | bool:
        """
        Checks if a local image has already been downloaded for the given entity
        Returns a string of the image's path if it exists
        Returns False if the image does not exist
        """
        if not isinstance(item_id, int):
            raise TypeError("item_id must be an integer.")
        if not isinstance(item_type, str):
            raise TypeError("item_type must be a string.")

        item_type = item_type.lower()
        valid_types = ["release", "artist", "label"]
        if item_type not in valid_types:
            raise ValueError(f"Invalid item_type: {item_type}. "
                             f"Must be one of the following strings: {', '.join(valid_types)}")

        result = glob.glob(f'static/img/{item_type}/{item_id}.*')
        if result:
            url = '/' + result[0].replace('databass/', '')
            return url
        else:
            return False
