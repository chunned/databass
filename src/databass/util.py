from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text
from sqlalchemy.exc import DataError
import glob
import gzip
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from .db.models import *
from .db.util import construct_item
from .db.operations import insert, update
from .api import Util, MusicBrainz

load_dotenv()

# TODO: attempt to remove this file; move functions into classes or modules where they fit
# img_exists can be part of database model class
# update_sequence probably can also be part of model class
# backup should be removed/redone entirely (it's only half done, works for running locally but not docker)


def img_exists(
        item_id: int,
        item_type: str
) -> str | bool:
    """
    Checks if a local image has already been downloaded for the given entity
    Returns a string of the image's path if it exists
    Returns False if the image does not exist
    """

    if not isinstance(item_id, int):
        raise TypeError("item_id must be an integer.")
    if not isinstance(item_type, str):
        raise TypeError("item_type must be a string.")

    item_type = item_type.lower()
    valid_types = ["release", "artist", "label"]
    if item_type not in valid_types:
        raise ValueError(f"Invalid item_type: {item_type}. "
                         f"Must be one of the following strings: {', '.join(valid_types)}")

    result = glob.glob(f'static/img/{item_type}/{item_id}.*')
    if result:
        url = '/' + result[0].replace('databass/', '')
        return url
    else:
        return False


def update_sequence(
        app: Flask,
        app_db: SQLAlchemy,
) -> None:
    """
    Updates the sequence number used for each table's primary key
    :param app: Flask application instance
    :param app_db: flask_sqlalchemy database instance
    :return: None
    """
    tables = ['release', 'label', 'artist']
    with app.app_context():
        with app_db.engine.connect() as conn:
            try:
                for table in tables:
                    conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), MAX(id)) FROM {table};"))
            except DataError:
                raise
            except Exception:
                raise


def backup():
    """
    Dumps database to disk; currently only works when running outside of Docker
    :return:
    """
    backup_file = f'databass_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gz'
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('PG_USER')

    if os.getenv('DOCKER'):
        pg_hostname = os.getenv('PG_HOSTNAME')
        command = f'sudo docker exec {pg_hostname} pg_dump -U {db_user} {db_name}'
    else:
        command = f'pg_dump -U {db_user} {db_name}'

    print(command)

    with gzip.open(backup_file, 'wb') as bkp:
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, universal_newlines=True)
        for line in iter(process.stdout.readline, ""):
            bkp.write(line.encode('utf-8'))
        process.stdout.close()
        process.wait()
    return backup_file


def get_stats():
    stats = {
        "total_listens": Release.total_count(),
        "total_artists": Artist.total_count(),
        "total_labels": Label.total_count(),
        "average_rating": Release.ratings_average(),
        "average_runtime": Release.average_runtime(),
        "total_runtime": Release.total_runtime(),
        "listens_this_year": Release.listens_this_year(),
        "listens_per_day": Release.listens_per_day(),
        "top_rated_labels": Label.average_ratings_bayesian()[0:10],
        "top_rated_artists": Artist.average_ratings_bayesian()[0:10],
        "top_frequent_labels": Label.frequency_highest()[0:10],
        "top_frequent_artists": Artist.frequency_highest()[0:10]
    }
    return stats

def create_if_not_exist(mbid: str, name: str, item_type: str) -> int:
    """
    Check if an item exists in the database, create the item if it does not exist
    :param mbid: MusicBrainzID of the item
    :param name: Item name
    :param item_type: "label" or "artist"
    :return: Database ID of the item
    """
    # Check if item exists already
    if item_type == 'label':
        item_exists = Label.exists_by_mbid(mbid)
    elif item_type == 'release':
        item_exists = Artist.exists_by_mbid(mbid)
    else:
        raise ValueError(f"Unsupported item_type: {item_type}")

    if item_exists:
        item_id = item_exists.id
    else:
        # Item does not exist; grab image, start/end date, type, and insert
        if item_type == 'label':
            item_search = MusicBrainz.label_search(name=name, mbid=mbid)
        elif item_type == 'release':
            item_search = MusicBrainz.artist_search(name=name, mbid=mbid)

        # Construct and insert label
        new_item = construct_item(item_type, item_search)
        item_id = insert(new_item)
        # TODO: see if Util.get_image() can be refactored; instead of label_name and artist_name use item_name
        if item_type == 'label':
            Util.get_image(
                item_type=item_type,
                item_id=item_id,
                label_name=name
            )
        elif item_type == 'release':
            Util.get_image(
                item_type=item_type,
                item_id=item_id,
                artist_name=name
            )
        # TODO: figure out a way to call Util.get_image() upon any insertion so it doesn't need to be manually called
    return item_id


def create_release(data: dict) -> int:
    """

    :param data:
    :return:
    """
    new_release = construct_item('release', data)
    release_id = insert(new_release)
    image_filepath = Util.get_image(
        item_type='release',
        item_id=release_id,
        release_name=data["name"],
        artist_name=data["artist_name"],
        label_name=data["label_name"],
        mbid=data["release_group_mbid"]
    )
    # TODO: see if the image field is still needed anywhere;
    new_release.image = image_filepath
    update(new_release)
    return new_release.id


def create_tags(tags: str, release_id: int) -> None:
    for tag in tags.split(','):
        tag_data = {"name": tag, "release_id": release_id}
        tag_obj = construct_item('tag', tag_data)
        insert(tag_obj)


def check_goals() -> None:
    active_goals = Goal.get_incomplete()
    if active_goals is not None:
        for goal in active_goals:
            goal.check_and_update_goal()
            if goal.end_actual:
                # Goal is complete; updating db entry
                update(goal)


def handle_submit_data(submit_data: dict) -> None:
    runtime = MusicBrainz.get_release_length(submit_data["mbid"])

    submit_data["runtime"] = runtime

    if submit_data["label_mbid"]:
        label_id = create_if_not_exist(
            mbid=submit_data["label_mbid"],
            name=submit_data["label_name"],
            item_type='label'
        )
    else:
        label_id = 0

    submit_data["label_id"] = label_id

    if submit_data["artist_mbid"]:
        artist_id = create_if_not_exist(
            mbid=submit_data["artist_mbid"],
            name=submit_data["artist_name"],
            item_type='artist'
        )
    else:
        artist_id = 0

    submit_data["artist_id"] = artist_id
    release_id = create_release(submit_data)

    if submit_data["tags"] is not None:
        create_tags(submit_data["tags"], release_id)

    check_goals()
