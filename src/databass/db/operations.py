from .base import app_db
from .util import get_model
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


def insert(item: SQLAlchemy.Model) -> int:
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


def update(item: SQLAlchemy.Model) -> None:
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
