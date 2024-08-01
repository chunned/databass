# Rewrite of db.py to use SQLAlchemy
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, func, extract
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
import datetime

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
        print('success')
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
    insert_item(new_release)


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
    insert_item(new_artist)


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
    insert_item(new_label)


def get_stats():
    current_year = str(datetime.datetime.now().year)
    days_this_year = datetime.date.today().timetuple().tm_yday
    stats = {"total_listens": db.session.query(Release.id).count(),
             "total_artists": db.session.query(Artist).count(),
             "total_labels": db.session.query(Label).count(),
             "average_rating": db.session.query(func.avg(Release.rating)).scalar(),
             "average_runtime": db.session.query(func.avg(Release.runtime)).scalar(),
             "total_runtime": db.session.query(func.sum(Release.runtime)).scalar(),
             "listens_this_year": db.session.query(func.count(Release.id)).filter(func.substr(Release.listen_date, 1, 4) == current_year).scalar(),
             }
    listens_per_day = stats["listens_this_year"] / days_this_year
    stats["listens_per_day"] = listens_per_day

    # Top rated labels
    query = (
        db.session.query(
            Label.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.label_id).label('release_count')
        )
        .join(Release, Release.label_id == Label.id)
        .filter(Label.name.notin_(['none', '[no label]']))  # Don't count the entries corresponding to no label for release
        .group_by(Label.name)
        .having(func.count(Release.label_id) != 1)          # Don't count labels with only 1 release
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        .limit(5)
        .all()
    )
    results = [{'label': row.name,
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
    results = [{'artist': row.name,
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
    results = [{'label': row.name,
                'count': row.count}
               for row in query]
    stats["frequent_labels"] = results
    print(results)

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
    results = [{'label': row.name,
                'count': row.count}
               for row in query]
    stats["frequent_artists"] = results
#    print(stats)

    return stats


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
