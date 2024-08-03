# Rewrite of db.py to use SQLAlchemy
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, func, extract
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
import datetime
import pytz
import os


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


db = SQLAlchemy(model_class=Base)


# --- Database models ---
class Release(db.Model):
    __tablename__ = "release"
    mbid: Mapped[Optional[str]] = mapped_column(String, unique=True)
    artist_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("artist.id"))
    label_id: Mapped[int] = mapped_column(sqlalchemy.ForeignKey("label.id"))
    title: Mapped[str] = mapped_column(String())
    release_year: Mapped[int] = mapped_column(Integer())
    runtime: Mapped[int] = mapped_column(Integer())
    rating: Mapped[int] = mapped_column(Integer())
    listen_date: Mapped[str] = mapped_column(String())
    track_count: Mapped[int] = mapped_column(Integer())
    country: Mapped[str] = mapped_column(String())
    genre: Mapped[str] = mapped_column(String())
    tags: Mapped[Optional[str]] = mapped_column(String())
    art: Mapped[Optional[str]] = mapped_column(String())

    def __init__(self, mbid: Optional[str] = None, artist_id: int = 0, label_id: int = 0, **kwargs):
        self.mbid = mbid
        self.artist_id = artist_id
        self.label_id = label_id
        for key, value in kwargs.items():
            setattr(self, key, value)


class ArtistOrLabel(db.Model):
    # Artist and Label tables are both built from this prototype
    __abstract__ = True
    mbid: Mapped[Optional[str]] = mapped_column(String(), unique=True)
    name: Mapped[str] = mapped_column(String())
    country: Mapped[Optional[str]] = mapped_column(String())
    type: Mapped[Optional[str]] = mapped_column(String())
    begin_date: Mapped[Optional[str]] = mapped_column(String())
    end_date: Mapped[Optional[str]] = mapped_column(String())
    image: Mapped[Optional[str]] = mapped_column(String())

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Label(ArtistOrLabel):
    __tablename__ = "label"


class Artist(ArtistOrLabel):
    __tablename__ = "artist"


# --- Database operation functions ---
def insert_item(item):
    try:
        db.session.add(item)
        db.session.commit()
        return item.id
    except sqlalchemy.exc.IntegrityError as err:
        db.session.rollback()
        print(f'SQLite Integrity Error: \n{err}\n')
    except Exception as err:
        db.session.rollback()
        print(f'Unexpected error: {err}')


def insert_release(release):
    new_release = Release(
        mbid=release.get("mbid"),
        artist_id=release.get("artist_id", 0),
        label_id=release.get("label_id", 0),
        title=release.get("title"),
        release_year=release.get("release_year", 0),
        runtime=release.get("runtime", 0),
        rating=release.get("rating"),
        listen_date=release.get("listen_date"),
        track_count=release.get("track_count"),
        country=release.get("country", 0),
        art=release.get("art", ''),
        genre=release.get("genre"),
        tags=release.get("tags", '')
    )
    release_id = insert_item(new_release)
    return release_id


def insert_artist(artist):
    new_artist = Artist(
        mbid=artist.get("mbid", "0"),
        name=artist.get("name"),
        country=artist.get("country", ""),
        type=artist.get("type", ""),
        begin_date=artist.get("begin_date", ""),
        end_date=artist.get("end_date", ""),
        image=artist.get("image")
    )
    artist_id = insert_item(new_artist)
    return artist_id


def insert_label(label):
    new_label = Label(
        mbid=label.get("mbid", "0"),
        name=label.get("name"),
        country=label.get("country", ""),
        type=label.get("type", ""),
        begin_date=label.get("begin_date", ""),
        end_date=label.get("end_date", ""),
        image=label.get("image")
    )
    label_id = insert_item(new_label)
    return label_id


def get_stats():
    local_timezone = pytz.timezone(os.getenv('TIMEZONE'))
    current_year = str(datetime.datetime.now(local_timezone).year)
    days_this_year = datetime.date.today().timetuple().tm_yday
    # Check if any releases are in the database. If not, skip stats
    db_length = db.session.query(func.count(Release.id)).scalar()
    if db_length == 0:
        return ''

    stats = {"total_listens": db.session.query(Release.id).count(),
             "total_artists": db.session.query(Artist).count(),
             "total_labels": db.session.query(Label).count(),
             "average_rating": db.session.query(
                 func.round(
                     func.avg(Release.rating), 2)
             ).scalar(),
             "average_runtime": round(
                 (
                         (
                             db.session.query(
                                 func.avg(
                                     Release.runtime
                                 )
                             ).scalar()
                         ) / 60000
                 ), 2
             ),
             "total_runtime": round(
                 (
                         (
                             db.session.query(
                                 func.sum(
                                     Release.runtime
                                 )
                             ).scalar()
                         ) / 3600000
                 ), 2
             ),
             "listens_this_year": db.session.query(func.count(Release.id)).filter(
                 func.substr(Release.listen_date, 1, 4) == current_year).scalar(),
             }
    listens_per_day = stats["listens_this_year"] / days_this_year
    stats["listens_per_day"] = round(listens_per_day, 2)

    # Top rated labels
    query = (
        db.session.query(
            Label.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.label_id).label('release_count')
        )
        .join(Release, Release.label_id == Label.id)
        .filter(
            Label.name.notin_(['none', '[no label]']))  # Don't count the entries corresponding to no label for release
        .group_by(Label.name)
        .having(func.count(Release.label_id) != 1)  # Don't count labels with only 1 release
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'average_rating': row.average_rating,
                'release_count': row.release_count}
               for row in query]
    stats["favourite_labels"] = results

    # Highest rated artists
    query = (
        db.session.query(
            Artist.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.artist_id).label('release_count')
        )
        .join(Release, Release.artist_id == Artist.id)
        .group_by(Artist.name)
        .having(func.count(Release.artist_id) != 1)
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'average_rating': row.average_rating,
                'release_count': row.release_count}
               for row in query]
    stats["favourite_artists"] = results

    # Most frequent labels
    query = (
        db.session.query(
            Label.name,
            func.count(Release.label_id).label('count')
        )
        .join(Release, Release.label_id == Label.id)
        .group_by(Label.name)
        .order_by(func.count(Release.label_id).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'count': row.count}
               for row in query]
    stats["frequent_labels"] = results

    # Most frequent artists
    query = (
        db.session.query(
            Artist.name,
            func.count(Release.artist_id).label('count')
        )
        .join(Release, Release.artist_id == Artist.id)
        .group_by(Artist.name)
        .order_by(func.count(Release.artist_id).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'count': row.count}
               for row in query]
    stats["frequent_artists"] = results

    return stats


def get_homepage_data():
    home_data = (
        db.session.query(
            Artist.name,
            Release.title,
            Release.rating,
            Release.listen_date,
            Release.genre,
            Release.art,
            Release.mbid,
            Release.tags
        )
        .join(Artist, Artist.id == Release.artist_id)
        .order_by(Release.listen_date.desc())
        .limit(10)  # when pagination is implemented this can be raised
    )
    return home_data


def get_items(item_type):
    # Gets all items of a specified type
    if item_type == 'releases':
        items = db.session.query(Release).all()
    elif item_type == 'artists':
        items = db.session.query(Artist).all()
    elif item_type == 'labels':
        items = db.session.query(Label).all()
    else:
        raise ValueError('ERROR: Invalid item_type: ', item_type)
    return items


def get_item(item_type, item_id):
    # Gets a single item specified by its ID
    if item_type == 'release':
        release = db.session.query(Release).where(Release.id == item_id)
        artist = db.session.query(Artist).where(Artist.id == item_id)
        label = db.session.query(Label).where(Label.id == item_id)
        item_data = {
            "release": release[0],
            "artist": artist[0],
            "label": label[0]
        }
    elif item_type == 'artist':
        artist = db.session.query(Artist).where(Artist.id == item_id).all()
        releases = (db.session.query(Release, Label.name)
                    .join(Label, Release.label_id == Label.id)
                    .join(Artist, Artist.id == Release.artist_id)
                    .where(Artist.id == item_id)
                    .all()
                    )
        item_data = {
            "artist": artist[0],
            "releases": releases
        }
    elif item_type == 'label':
        label = db.session.query(Label).where(Label.id == item_id).all()
        releases = (db.session.query(Release, Artist)
                    .join(Artist, Artist.id == Release.artist_id)
                    .where(Release.label_id == item_id)
                    ).all()
        item_data = {
            "label": label[0],
            "releases": releases
        }
    else:
        raise ValueError('ERROR: Invalid item_type: ', item_type)
    return item_data


def exists(mbid, item_type):
    # mbid = the MusicBrainz ID for the entity
    # item_type = release, artist, or label
    # Returns a 2 element array:
    # - 1: True if an item exists in the database, False otherwise
    # - 2: Item's ID (primary key) in the database if it exists, None otherwise
    if item_type == 'label':
        q = db.session.query(Label.id).where(Label.mbid == mbid).scalar()
    elif item_type == 'artist':
        q = db.session.query(Artist.id).where(Artist.mbid == mbid).scalar()
    elif item_type == 'release':
        q = db.session.query(Release.id).where(Release.mbid == mbid).scalar()
    else:
        raise ValueError('Invalid item_type passed')
    if q:
        return [True, q]
    else:
        return [False, q]


# ---- INCOMPLETE -----
def update_release():
    return 0


def update_artist():
    return 0


def update_label():
    return 0


# below should maybe be moved elsewhere
def get_missing_covers():
    return 0


def get_missing_artist_data():
    return 0


def get_missing_label_data():
    return 0
