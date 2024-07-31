# Rewrite of db.py to use SQLAlchemy
import sqlalchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)


db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///alchemy.db"
db.init_app(app)


# Database models
class Release(db.Model):
    __tablename__ = "release"
    mbid: Mapped[Optional[str]] = mapped_column(String(), unique=True)
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


class ArtistOrLabel(db.Model):
    # Artist and Label tables are both built from this prototype
    __abstract__ = True
    mbid: Mapped[str] = mapped_column(String(), unique=True)
    name: Mapped[str] = mapped_column(String())
    country: Mapped[str] = mapped_column(String())
    type: Mapped[str] = mapped_column(String())
    begin_date: Mapped[Optional[str]] = mapped_column(String())
    end_date: Mapped[Optional[str]] = mapped_column(String())
    image: Mapped[Optional[str]] = mapped_column(String())


class Label(db.Model):
    __tablename__ = "label"


class Artist(db.Model):
    __tablename__ = "artist"


# create all models/tables after defining them
# with app.app_context():
#   db.create_all()