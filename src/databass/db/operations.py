from .base import app_db
from .util import get_model
from .models import Artist, Label, Release
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
from os import getenv
from pytz import timezone
from datetime import datetime

load_dotenv()
TIMEZONE = getenv('TIMEZONE')


def insert(item: app_db.Model) -> int:
    """
    Insert an instance of a model class into the database
    :param item: Instance of SQLAlchemy model class from models.py
    :return: ID of the newly inserted item on success; -1 on failure
    """
    try:
        app_db.session.add(item)
        app_db.session.commit()
        return item.id
    # TODO: investigate other common exceptions stemming from .insert()
    except IntegrityError as err:
        app_db.session.rollback()
        raise IntegrityError(f'SQLite Integrity Error: \n{err}\n', params=err.params, orig=err)
    except Exception as err:
        app_db.session.rollback()
        raise Exception(f'Unexpected error: {err}')


def update(item: app_db.Model) -> None:
    """
    Update an existing database entry
    :param item: Instance of database model class to update
    """
    try:
        app_db.session.merge(item)
        app_db.session.commit()
        # TODO: investigate common exceptions stemming from .merge()
    except Exception as err:
        app_db.session.rollback()
        raise Exception(f'Unexpected error: {err}')

def delete(item_type: str,
           item_id: str) -> None:
    """
    Delete an existing entry from the database
    :param item_type: String corresponding to a database model class
    :param item_id: The ID of the item to delete
    """
    # TODO: investigate common exceptions stemming from .delete()
    try:
        model = get_model(item_type)
        if model:
            to_delete = app_db.session.query(model).where(model.id == item_id).one()
            if to_delete:
                app_db.session.delete(to_delete)
                app_db.session.commit()
            else:
                raise Exception(f'No {item_type} entry found for {item_id}')
        else:
            raise NameError(f"No model found for item_type: {item_type}")
    except Exception as err:
        app_db.session.rollback()
        raise Exception(f'Unexpected error: {err}')


def submit_manual(data):
    # TODO: evaluate whether this can be removed and just use insert(); need to compare with util.handle_submit_data()
    label_name = data["label_name"]
    existing_label = Label.exists_by_name(name=label_name)
    # existing_label = exists(item_type='label', name=label_name)
    if existing_label is not None:
        label_id = existing_label.id
    else:
        label = Label()
        label.name = label_name
        label_id = insert(label)

    artist_name = data["artist_name"]
    existing_artist = Artist.exists_by_name(name=artist_name)
    # existing_artist = exists(item_type='artist', name=artist_name)
    if existing_artist is not None:
        artist_id = existing_artist.id
    else:
        artist = Artist()
        artist.name = artist_name
        artist_id = insert(artist)

    local_timezone = timezone(TIMEZONE)

    release = Release()
    release.name = data["name"]
    release.artist_id = artist_id
    release.label_id = label_id
    release.release_year = data["release_year"]
    release.rating = data["rating"]
    release.genre = data["genre"]
    release.tags = data["tags"]
    release.image = data["image"]
    release.listen_date = datetime.now(local_timezone).strftime("%Y-%m-%d")
    insert(release)
