from flask import Flask
import routes
import util
import os
from models import app_db
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_connection_string = f'postgresql://{db_user}:{db_password}@localhost/{db_name}'


class Config:
    SECRET_KEY = uuid4().hex
    SQLALCHEMY_DATABASE_URI = db_connection_string
    DISCOGS_KEY = os.environ.get('DISCOGS_KEY')
    DISCOGS_SECRET = os.environ.get('DISCOGS_SECRET')
    TIMEZONE = os.environ.get('TIMEZONE')
    STATIC_FOLDER = 'static'
    DEBUG = True


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    routes.register_routes(app)
    util.register_filters(app)

    app_db.init_app(app)
    print('DB initialized')
    with app.app_context():
        app_db.create_all()
        print('Tables created')
    return app


if __name__ == '__main__':
    app = create_app()

    app.run(
        debug=True,
        host='0.0.0.0',
        port=8080
    )
