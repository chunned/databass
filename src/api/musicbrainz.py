import musicbrainzngs as mbz
import musicbrainzngs.musicbrainz

from .util import Util
from dateutil import parser as dateparser
from dotenv import load_dotenv
from os import getenv

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
    def release_search(release: str = None,
                       artist: str = None,
                       label: str = None):
        """
        Search MusicBrainz for releases matching the search terms
        :param release: Optional - release name string
        :param artist: Optional - artist name string
        :param label: Optional - label name string
        :return: Dictionary containing data from API
        """
        if MusicBrainz.init:
            results = mbz.search_releases(artist=artist,
                                          label=label,
                                          release=release)
            search_data = []        # Will hold the main return data
            for r in results["release-list"]:
                try:
                    labelinfo = r["label-info-list"][0]["label"]
                    try:
                        label_id = labelinfo["id"]
                    except Exception:
                        label_id = ""
                    try:
                        label_name = labelinfo["name"]
                    except Exception:
                        label_name = ""
                except Exception:
                    label_id = ""
                    label_name = ""
                label = {
                    "mbid": label_id,
                    "name": label_name
                }
                try:
                    raw_date = r["date"]
                    date = dateparser.parse(raw_date, fuzzy=True).year
                except Exception:
                    date = ""
                try:
                    physical_release = r["medium-list"][0]
                    try:
                        release_format = physical_release["format"]
                    except Exception:
                        release_format = ""
                    try:
                        track_count = physical_release["track-count"]
                    except Exception:
                        track_count = ""
                except Exception:
                    release_format = ""
                    track_count = ""
                try:
                    country = r["country"]
                except Exception:
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
    def parse_search_result(search_result: dict):
        # Parses the result of get_(artist|label)_by_id and returns a dictionary
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
    def get_release_length(mbid: str):
        """
        Search a release on MusicBrainz and calculate the runtime (ms)
        :param mbid: String containing the MBID of the release
        :return: Integer representing the release runtime in ms
        """
        if MusicBrainz.init:
            try:
                release_data = mbz.get_release_by_id(mbid,
                                                     includes=["recordings", "media", "recording-level-rels"])
                print(release_data)
                tracks = release_data["release"]["medium-list"][0]["track-list"]
                print(tracks)
                length = 0
                try:
                    for track in tracks:
                        length += track["length"]
                except TypeError:
                    length = 0
            except Exception as e:
                raise e
            return length
        else:
            MusicBrainz.initialize()
            MusicBrainz.get_release_length(mbid)

    @staticmethod
    def get_image(mbid: str):
        """
        Search CoverArtArchive API for image candidates
        :param mbid: MBID of the release/release group to check for existing images
        :return: List of available image URLs
        """
        try:
            return mbz.get_release_group_image_front(mbid, size='250')
        except musicbrainzngs.musicbrainz.ResponseError:
            try:
                covers = mbz.get_image_list(mbid)
                if covers:
                    coverid = covers['images'][0]['id']
                    return mbz.get_image(mbid, coverid=coverid, size='250')
            except musicbrainzngs.musicbrainz.ResponseError:
                return None
            except Exception as e:
                raise e
        except Exception as e:
            raise e

