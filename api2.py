import musicbrainzngs as mbz
from dateutil import parser as dateparser

mbz.set_useragent('Databass', 'v0.4.5', contact='https://github.com/chunned/databass')


def search(release=None, artist=None, label=None):
    results = mbz.search_releases(artist=artist,
                                  label=label,
                                  release=release)
    search_data = []        # Will hold the main return data
    backup_mbids = []       # Holds all release MBIDs found during search; used for fetching images
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
            area = r["country"]
        except Exception:
            area = ""

        release_id = r["id"]
        backup_mbids.append(release_id)
        length = get_release_length(release_id)

        rel = {
            "release": {
                "name": release_id,
                "mbid": r["id"]
            },
            "artist": {
                "name": r["artist-credit"][0]["name"],
                "mbid": r["artist-credit"][0]["artist"]["id"]
            },
            "label": label,
            "date": date,
            "format": release_format,
            "track-count": track_count,
            "length": length,
            "area": area,
            "backup_mbids": backup_mbids
        }
        search_data.append(rel)
    return search_data


def get_release_length(mbid):
    try:
        release_data = mbz.get_release_by_id(mbid,
                                             includes=["recordings", "media", "recording-level-rels"])
        tracks = release_data["release"]["medium-list"][0]["track-list"]
        length = 0
        try:
            for track in tracks:
                length += track["length"]
        except TypeError:
            length = 0
    except Exception:
        raise Exception
    return length

a = 'Michael Jackson'
b = 'Thriller'
x = search(artist=a, release=b)

# z = 'abe08d65-07ba-4a9e-acde-82cb375073c9'
# get_release_length(z)