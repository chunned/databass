from flask import url_for
import os
from sqlalchemy import text
from sqlalchemy.exc import DataError
import glob
import gzip
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def img_exists(item_id, item_type):
    result = glob.glob(f'static/img/{item_type}/{item_id}.*')
    if result:
        url = '/' + result[0].replace('databass/')
        return url
    else:
        return result


def register_filters(app):
    @app.template_filter('img_exists')
    def img_exists_filter(item_id, item_type):
        exists = img_exists(item_id, item_type)
        if exists:
            img_uri = exists.replace("./databass", "")
            print(img_uri)
            return img_uri
        else:
            return None


def update_sequence(app, app_db):
    with app.app_context():
        with app_db.engine.connect() as conn:
            try:
                conn.execute(text("SELECT setval(pg_get_serial_sequence('release', 'id'), MAX(id)) FROM release;"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('artist', 'id'), MAX(id)) FROM artist;"))
                conn.execute(text("SELECT setval(pg_get_serial_sequence('label', 'id'), MAX(id)) FROM label;"))
            except DataError:
                pass


def backup():
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