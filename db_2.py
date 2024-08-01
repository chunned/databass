# Rewrite of db.py to use SQLAlchemy
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


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
    db.session.add(new_release)
    db.session.commit()
    return 'success'


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

    db.session.add(new_artist)
    db.session.commit()
    return 'success'


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
    db.session.add(new_label)
    db.session.commit()
    return 'success'
