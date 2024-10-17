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


def backup():
    """
    Dumps database to disk; currently only works when running outside of Docker
    :return:
    """
    # TODO: rewrite or remove
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


def handle_submit_data(submit_data: dict) -> None:
    # TODO: figure out a better place for this function to live
    from db.models import Goal, Tag, Release, Artist, Label
    runtime = MusicBrainz.get_release_length(submit_data["mbid"])

    submit_data["runtime"] = runtime

    if submit_data["label_mbid"]:
        label_id = Label.create_if_not_exist(
            mbid=submit_data["label_mbid"],
            name=submit_data["label_name"],
        )
    else:
        label_id = 0

    submit_data["label_id"] = label_id

    if submit_data["artist_mbid"]:
        artist_id = Artist.create_if_not_exist(
            mbid=submit_data["artist_mbid"],
            name=submit_data["artist_name"],
        )
    else:
        artist_id = 0

    submit_data["artist_id"] = artist_id
    release_id = Release.create_new(submit_data)

    if submit_data["tags"] is not None:
        Tag.create_tags(submit_data["tags"], release_id)
    Goal.check_goals()
