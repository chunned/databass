# create a script that selects all entries from sqlite db and inserts into a given postgres db

# eventually turn this into a command that can be run `docker compose up migrate` but for now just worry about the db part

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import os
from datetime import datetime
import old_models
import models


def migrate():
    load_dotenv()
    db = os.getenv('SQLITE_DB')
    user = os.getenv('PG_USER')
    password = os.getenv('PG_PASSWORD')
    pg_db = os.getenv('DB_NAME')
    db_hostname = os.getenv('PG_HOSTNAME')
    cmd = f"createdb {pg_db}"
    try:
        os.system(cmd)
    except Exception:
        print("Unable to create database")

    sqlite_db = f"sqlite:///{db}"
    sqlite_engine = create_engine(sqlite_db)
    SQLite_Session = sessionmaker(bind=sqlite_engine)
    sqlite_session = SQLite_Session()


    postgres_db = f"postgresql://{user}:{password}@{db_hostname}/{pg_db}"
    pg_engine = create_engine(postgres_db)
    PG_Session = sessionmaker(bind=pg_engine)
    pg_session = PG_Session()

    # Create PG tables
    models.Base.metadata.create_all(pg_engine)

    # Artist and Label with ID = 0 need to be created manually
    pg_session.add(
        models.Label(
            id=0,
            name="[NONE]",
        )
    )
    pg_session.add(
        models.Artist(
            id=0,
            name="[NONE]",
        )
    )
    try:
        pg_session.commit()
    except IntegrityError:
        pg_session.rollback()
        pass

    labels = sqlite_session.query(old_models.Label).all()
    for label in labels:
        new_label = models.Label(
            id=label.id,
            mbid=label.mbid,
            name=label.name,
            country=label.country,
            type=label.type,
            begin_date=label.begin_date,
            end_date=label.end_date,
            image=label.image
        )
        try:
            pg_session.add(new_label)
            pg_session.commit()
        except IntegrityError as err:
            pg_session.rollback()
            if 'already exists' in str(err):
                pass
            else:
                print('Integrity error for label: ', new_label)
                print(err)

    artists = sqlite_session.query(old_models.Artist).all()
    for artist in artists:
        new_artist = models.Artist(
            id=artist.id,
            mbid=artist.mbid,
            name=artist.name,
            country=artist.country,
            type=artist.type,
            begin_date=artist.begin_date,
            end_date=artist.end_date,
            image=artist.image
        )

        try:
            pg_session.add(new_artist)
            pg_session.commit()
        except IntegrityError as err:
            pg_session.rollback()
            if 'already exists' in str(err):
                pass
            else:
                print('Integrity error for artist: ', new_artist)
                print(err)

    releases = sqlite_session.query(old_models.Release).all()
    for release in releases:
        # create instance of new_models.Release with release.listen_date changed to datetime
        old_date = release.listen_date
        try:
            listen_date = datetime.strptime(old_date, "%Y-%m-%d")
        except TypeError:
            listen_date = datetime(9999, 12, 31, 23, 59, 59)

        year = release.release_year
        if isinstance(year, str):
            year = 0

        rating = release.rating
        if isinstance(rating, str):
            rating = 0

        runtime = release.runtime
        if not runtime:
            runtime = 0

        track_count = release.track_count
        if not track_count:
            track_count = 0

        country = release.country
        if not country:
            country = "Unknown"

        new_release = models.Release(
            id=release.id,
            mbid=release.mbid,
            artist_id=release.artist_id,
            label_id=release.label_id,
            name=release.name,
            release_year=year,
            runtime=runtime,
            rating=rating,
            listen_date=listen_date,
            track_count=track_count,
            country=country,
            genre=release.genre,
            tags=release.tags,
            image=release.image,
            review=release.review
        )
        try:
            pg_session.add(new_release)
            pg_session.commit()
        except IntegrityError as err:
            pg_session.rollback()
            if 'already exists' in str(err):
                pass
            else:
                print('Integrity error for release: ', new_release)
                print(err)

    pg_session.close()
    sqlite_session.close()
    print('Complete')
    return 0
