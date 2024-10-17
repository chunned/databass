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
