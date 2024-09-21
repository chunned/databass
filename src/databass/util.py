from flask import url_for
import os
from sqlalchemy import text
from sqlalchemy.exc import DataError
import glob


def img_exists(item_id, item_type):
    result = glob.glob(f'static/img/{item_type}/{item_id}.*')
    if result:
        url = '/' + result[0]
        return url
    else:
        return result


def register_filters(app):
    @app.template_filter('img_exists')
    def img_exists_filter(item_id, item_type):
        return img_exists(item_id, item_type)


def update_sequence(app, app_db):
    with app.app_context():
        with app_db.engine.connect() as conn:
            try:
                conn.execute(text("SELECT setval(pg_get_serial_sequence('release', 'id'), MAX(id)) FROM release;"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('artist', 'id'), MAX(id)) FROM artist;"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('label', 'id'), MAX(id)) FROM label;"))
            except DataError:
                pass


