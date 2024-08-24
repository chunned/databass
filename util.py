from flask import url_for
import os
from api import get_image_type_from_url, download_image
from db import get_all_id_and_img
from sqlalchemy import text
from sqlalchemy.exc import DataError


def download_all_missing_images(app):
    with app.app_context():
        print('INFO: Fetching all missing images')
        data = get_all_id_and_img()
        for rel in data["releases"]:
            print(f'INFO: Release ID: {rel[0]}, Image URL: {rel[1]}')
            if not img_exists(
                    item_id=rel[0],
                    item_type='release',
                    img_url=rel[1]
            ):
                print('INFO: Fetching image...')
                download_image(
                    item_type='release',
                    item_id=rel[0],
                    img_url=rel[1]
                )
            else:
                print('INFO: Image already exists')
        for lab in data["labels"]:
            print(f'INFO: Label ID: {lab[0]}, Image URL: {lab[1]}')
            if not img_exists(
                    item_id=lab[0],
                    item_type='label',
                    img_url=lab[1]
            ):
                print('INFO: Fetching image...')
                download_image(
                    item_type='label',
                    item_id=lab[0],
                    img_url=lab[1]
                )
            else:
                print('INFO: Image already exists')
        for art in data["artists"]:
            print(f'INFO: Artist ID: {art[0]}, Image URL: {art[1]}')
            if not img_exists(
                    item_id=art[0],
                    item_type='artist',
                    img_url=art[1]
            ):
                print('INFO: Fetching image...')
                download_image(
                    item_type='artist',
                    item_id=art[0],
                    img_url=art[1]
                )
            else:
                print('INFO: Image already exists')


def img_exists(item_id, item_type, img_url):
    extension = get_image_type_from_url(img_url)
    # print(f'INFO: Checking if image exists for {item_type} {item_id}{extension}')
    path = os.path.join('static/img', item_type, f'{item_id}{extension}')
    # print(f'INFO: Checking path: {path}')
    result = os.path.isfile(path)
    # print(f'INFO: {result}')
    if result:
        url = url_for('static', filename=f'img/{item_type}/{item_id}{extension}')
        # print(f'INFO: Returning {url}')
        return url
    else:
        return result


def register_filters(app):
    @app.template_filter('img_exists')
    def img_exists_filter(item_id, item_type, img_url):
        return img_exists(item_id, item_type, img_url)


def update_sequence(app, app_db):
    with app.app_context():
        with app_db.engine.connect() as conn:
            try:
                conn.execute(text("SELECT setval(pg_get_serial_sequence('release', 'id'), MAX(id)) FROM release;"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('artist', 'id'), MAX(id)) FROM artist;"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('label', 'id'), MAX(id)) FROM label;"))
            except DataError:
                pass
