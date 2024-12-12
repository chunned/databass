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
    Insert a new database entry.

    Args:
        item (app_db.Model): Instance of a database model class to insert.

    Returns:
        int: The ID of the newly inserted item.

    Raises:
        IntegrityError: If there is a SQLite integrity error when inserting the item.
        Exception: For any other unexpected errors.
    """
    try:
        app_db.session.add(item)
        app_db.session.commit()
        return item.id
    except IntegrityError as err:
        app_db.session.rollback()
        raise IntegrityError(f'SQLite Integrity Error: \n{err}\n', params=err.params, orig=err)
    except Exception as err:
        app_db.session.rollback()
        raise Exception(f'Unexpected error: {err}')


def update(item: app_db.Model) -> None:
    """
        Update an existing database entry.

        Args:
            item (app_db.Model): Instance of a database model class to update.

        Raises:
            Exception: For any unexpected errors that occur during the update operation.
    """
    try:
        model_class = type(item)
        existing_item = app_db.session.query(model_class).get(item.id)
        if existing_item:
            for key in item.__dict__:
                if not key.startswith('_'): # Ignore private attributes
                    setattr(existing_item, key, getattr(item, key))
            app_db.session.commit()
        else:
            raise Exception(f"No entry found with ID {item.id}")
    except Exception as err:
        app_db.session.rollback()
        raise Exception(f'Unexpected error: {err}')



def delete(item_type: str,
           item_id: str) -> None:
    """
        Delete a database entry by its type and ID.

        Args:
            item_type (str): The type of the database item to delete (e.g. 'label', 'artist').
            item_id (str): The ID of the database item to delete.

        Raises:
            Exception: If no model is found for the given item_type, or if an unexpected error occurs during the delete operation.
    """
    try:
        model = get_model(item_type)
        to_delete = app_db.session.query(model).where(model.id == item_id).one()
        if to_delete:
            app_db.session.delete(to_delete)
            app_db.session.commit()
        else:
            raise Exception(f'No {item_type} entry found for {item_id}')
    except Exception as err:
        app_db.session.rollback()
        raise Exception(f'Unexpected error: {err}')
