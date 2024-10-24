import musicbrainzngs as mbz
import musicbrainzngs.musicbrainz

from .util import Util
from dateutil import parser as dateparser
from dotenv import load_dotenv
from os import getenv
from typing import Optional, Dict, Any

load_dotenv()
VERSION = getenv("VERSION")


class MusicBrainz:
    init = False

    @classmethod
    def initialize(cls):
        if not cls.init:
            mbz.set_useragent('Databass', f'v{VERSION}', contact='https://github.com/chunned/databass')
            cls.init = True

    @staticmethod
    def release_search(
            release: str = None,
            artist: str = None,
            label: str = None
    ) -> list:
        """
        Search MusicBrainz for releases matching the search terms
        :param release: Optional - release name string
        :param artist: Optional - artist name string
        :param label: Optional - label name string
        :return: List of dictionary data results from API
        """
        if MusicBrainz.init:
            if all(search_term is None for search_term in (release, artist, label)):
                raise ValueError("At least one query term is required")
            results = mbz.search_releases(
                artist=artist,
                label=label,
                release=release
            )
            search_data = []        # Will hold the main return data
            for r in results["release-list"]:
                # Parse label data
                try:
                    labelinfo = r["label-info-list"][0]["label"]
                    try:
                        label_id = labelinfo["id"]
                    except KeyError:
                        label_id = ""
                    try:
                        label_name = labelinfo["name"]
                    except KeyError:
                        label_name = ""
                except (KeyError, IndexError):
                    # No label info found; continue with empty label data
                    label_id = ""
                    label_name = ""
                label = {
                    "mbid": label_id,
                    "name": label_name
                }
                try:
                    raw_date = r["date"]
                    date = dateparser.parse(raw_date, fuzzy=True).year
                except (KeyError, dateparser.ParserError):
                    date = ""
                try:
                    physical_release = r["medium-list"][0]
                    try:
                        release_format = physical_release["format"]
                    except KeyError:
                        release_format = ""
                    try:
                        track_count = 0
                        for disc in r["medium-list"]:
                            track_count += disc["track-count"]
                    except KeyError:
                        track_count = ""
                except (KeyError, IndexError):
                    release_format = ""
                    track_count = ""
                try:
                    country = r["country"]
                except KeyError:
                    country = ""

                release_id = r["id"]

                rel = {
                    "release": {
                        "name": r["title"],
                        "mbid": release_id
                    },
                    "artist": {
                        "name": r["artist-credit"][0]["name"],
                        "mbid": r["artist-credit"][0]["artist"]["id"]
                    },
                    "label": label,
                    "date": date,
                    "format": release_format,
                    "track_count": track_count,
                    "country": country,
                    "release_group_id": r["release-group"]["id"],
                }
                search_data.append(rel)
            return search_data
        else:
            MusicBrainz.initialize()
            return MusicBrainz.release_search(release, artist, label)

    @staticmethod
    def label_search(name: str, mbid: str = None):
        """
        Search MusicBrainz for labels matching the search terms
        :param name: Label name
        :param mbid: Optional - MBID of the label
        :return: Dictionary that can be used to construct an instance of Label from models.py
        """
        if MusicBrainz.init:
            if mbid is not None:
                try:
                    # If we have MBID, we can query the label directly
                    label_result = mbz.get_label_by_id(mbid, includes=['area-rels'])["label"]
                    label = MusicBrainz.parse_search_result(label_result)
                    return label
                except Exception as e:
                    raise e
            else:
                # No MBID, have to search. Assume first result is correct
                label_results = mbz.search_labels(query=name)
                try:
                    label_id = label_results["label-list"][0]["id"]
                    # Now that we have an MBID, recursively call this function using that ID to grab the label data
                    # This call is required because begin_date/end_date are not included in search results
                    MusicBrainz.label_search(name=name, mbid=label_id)
                except Exception as e:
                    raise e
        else:
            # MusicBrainz class not initialized; call initialize function, then re-call function
            MusicBrainz.initialize()
            return MusicBrainz.label_search(name, mbid)

    @staticmethod
    def artist_search(name: str, mbid: str = None):
        """
        Search MusicBrainz for artists matching the search terms
        :param name: Artist name
        :param mbid: Optional - MBID of the artist
        :return: Dictionary that can be used to construct an instance of Artist from models.py
        """
        if MusicBrainz.init:
            if mbid is not None:
                try:
                    # If we have MBID, we can query the label directly
                    artist_result = mbz.get_artist_by_id(mbid, includes=['area-rels'])["artist"]
                    artist = MusicBrainz.parse_search_result(artist_result)
                    return artist
                except Exception as e:
                    raise e
            else:
                # No MBID, have to search. Assume first result is correct
                artist_results = mbz.search_artists(query=name)
                try:
                    artist_id = artist_results["artist-list"][0]["id"]
                    # Now that we have an MBID, recursively call this function using that ID to grab the label data
                    # This call is required because begin_date/end_date are not included in search results
                    MusicBrainz.artist_search(name=name, mbid=artist_id)
                except Exception as e:
                    raise e
        else:
            # MusicBrainz class not initialized; call initialize function, then re-call function
            MusicBrainz.initialize()
            return MusicBrainz.artist_search(name, mbid)

    @staticmethod
    def parse_search_result(search_result: dict) -> dict:
        """
        Parse a search result from the MusicBrainz API into a dictionary with the following keys:
        - name: The name of the item (e.g. label, artist)
        - mbid: The MusicBrainz ID of the item
        - begin_date: The start date of the item, as a datetime object or None if not available
        - end_date: The end date of the item, as a datetime object or None if not available
        - country: The country of the item, or None if not available
        - type: The type of the item (e.g. "Label", "Artist"), or None if not available

        Args:
            search_result (dict): The raw search result dictionary from the MusicBrainz API.

        Returns:
            dict: A dictionary containing the parsed information about the item.
        """
        try:
            # Try to get the label's creation date
            begin_raw = search_result["life-span"]["begin"]
        except KeyError:
            begin_raw = None
        try:
            # Try to get the label's end date
            end_raw = search_result["life-span"]["end"]
        except KeyError:
            end_raw = None
            # Parse from string to datetime
        begin_date = Util.to_date('begin', begin_raw)
        end_date = Util.to_date('end', end_raw)

        try:
            country = search_result["country"]
        except KeyError:
            country = None

        try:
            item_type = search_result["type"]
        except KeyError:
            item_type = None

        item = {
            "name": search_result["name"],
            "mbid": search_result["id"],
            "begin_date": begin_date,
            "end_date": end_date,
            "country": country,
            "type": item_type,
        }
        return item

    @staticmethod
    def get_release_length(mbid: str) -> int:
        """
        Get the total length of a release on MusicBrainz in milliseconds.

        Args:
            mbid (str): The MBID (MusicBrainz ID) of the release.

        Returns:
            int: The total length of the release in milliseconds, or 0 if the length could not be determined.
        """
        if not mbid or not isinstance(mbid, str):
            return 0
        if MusicBrainz.init:
            try:
                release_data = mbz.get_release_by_id(mbid,
                                                     includes=["recordings", "media", "recording-level-rels"])
                tracks = [
                    track
                    for disc in release_data["release"]["medium-list"]
                    for track in disc["track-list"]
                ]
                length = 0
                for track in tracks:
                    try:
                        length += int(track["length"])
                    except (KeyError, TypeError) as e:
                        pass
                    finally:
                        return length
            except Exception as e:
                return 0
        else:
            MusicBrainz.initialize()
            return MusicBrainz.get_release_length(mbid)

    @staticmethod
    def get_image(mbid: str, size: str = '250') -> Optional[bytes]:
        """
        Search for the front cover image of a release group on MusicBrainz and return it as bytes, or return None if no image is found.

        Args:
            mbid (str): The MBID (MusicBrainz ID) of the release group.
            size (str): Desired size of the image in pixels, 250px by default

        Returns:
            Optional[bytes]: The front cover image of the release group as bytes, or None if no image is found.
        """
        if not mbid or not isinstance(mbid, str):
            return None
        try:
            return mbz.get_release_group_image_front(mbid, size=size)
        except musicbrainzngs.musicbrainz.ResponseError:
            try:
                covers: Dict[str, Any] = mbz.get_image_list(mbid)
                if covers:
                    try:
                        coverid = covers['images'][0]['id']
                        return mbz.get_image(mbid, coverid=coverid, size=size)
                    except KeyError:
                        pass
            except musicbrainzngs.musicbrainz.ResponseError:
                return None
        except Exception as e:
            return None

