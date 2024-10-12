from flask import Flask, g
import os
from dotenv import load_dotenv
from .db.base import app_db
from .routes import register_routes


load_dotenv()
VERSION = os.environ.get('VERSION')
print(f'App version: {VERSION}')


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    app.static_folder = 'static'
    app_db.init_app(app)

    with app.app_context():
        app_db.create_all()

        from .releases.routes import release_bp
        app.register_blueprint(release_bp)

        from .artists.routes import artist_bp
        app.register_blueprint(artist_bp)

        from .labels.routes import label_bp
        app.register_blueprint(label_bp)

        register_routes(app)

        @app.before_request
        def before_request():
            g.app_version = VERSION
        return app