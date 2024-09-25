from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, func, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime, date
from db.base import app_db

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


app_db.Model = Base


class Release(app_db.Model):
    __tablename__ = "release"
    id: Mapped[int] = mapped_column(primary_key=True)
    mbid: Mapped[Optional[str]] = mapped_column(String, unique=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artist.id"))
    label_id: Mapped[int] = mapped_column(ForeignKey("label.id"))
    name: Mapped[str] = mapped_column(String())
    release_year: Mapped[int] = mapped_column(Integer())
    runtime: Mapped[int] = mapped_column(Integer())
    rating: Mapped[int] = mapped_column(Integer())
    listen_date: Mapped[datetime] = mapped_column(DateTime())
    track_count: Mapped[int] = mapped_column(Integer())
    country: Mapped[str] = mapped_column(String())
    genre: Mapped[str] = mapped_column(String())
    tags: Mapped[Optional[str]] = mapped_column(String())
    image: Mapped[Optional[str]] = mapped_column(String())

    tag_list = relationship("Tag", back_populates="release", cascade="all, delete-orphan")
    # Below is deprecated; can be removed, but need to deal with existing entries
    review: Mapped[Optional[str]] = mapped_column(String())

    def __init__(self, mbid: Optional[str] = None, artist_id: int = 0, label_id: int = 0, **kwargs):
        self.mbid = mbid
        self.artist_id = artist_id
        self.label_id = label_id
        for key, value in kwargs.items():
            setattr(self, key, value)


class ArtistOrLabel(app_db.Model):
    # Artist and Label tables are both built from this prototype
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    mbid: Mapped[Optional[str]] = mapped_column(String(), unique=True)
    name: Mapped[str] = mapped_column(String())
    country: Mapped[Optional[str]] = mapped_column(String())
    type: Mapped[Optional[str]] = mapped_column(String())
    begin_date: Mapped[Optional[datetime.date]] = mapped_column(Date())
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date())
    image: Mapped[Optional[str]] = mapped_column(String())

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Label(ArtistOrLabel):
    __tablename__ = "label"


class Artist(ArtistOrLabel):
    __tablename__ = "artist"


class Goal(app_db.Model):
    __tablename__ = "goal"
    id: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[datetime] = mapped_column(DateTime())
    end_goal: Mapped[datetime] = mapped_column(DateTime())
    end_actual: Mapped[Optional[datetime]] = mapped_column(DateTime())
    type: Mapped[str] = mapped_column(String()) # i.e. Releases, Albums, Labels
    amount: Mapped[int] = mapped_column(Integer())

    @property
    def new_releases_since_start_date(self):
        return (
            app_db.session.query(func.count(Release.id))
            .filter(Release.listen_date >= self.start_date)
            .scalar()
        )

    def check_and_update_goal(self):
        print(f'Target amount: {self.amount} - Actual amount: {self.new_releases_since_start_date}')
        if self.type == 'release':
            if self.new_releases_since_start_date >= self.amount:
                print('Updating end_actual to current time')
                self.end_actual = datetime.now()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)


class Review(app_db.Model):
    __tablename__ = "review"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("release.id"))
    timestamp: Mapped[date] = mapped_column(DateTime, default=func.now())
    text: Mapped[str] = mapped_column(String())


class Tag(app_db.Model):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("release.id"))
    name: Mapped[str] = mapped_column(String())

    release = relationship("Release", back_populates="tag_list")

    __table_args__ = (
        # Make sure release can't have multiple of the same tag
        UniqueConstraint('release_id', 'name', name='unique_release_tag'),
    )
