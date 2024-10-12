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

load_dotenv()


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
