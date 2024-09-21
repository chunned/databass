from flask import Flask, g
import os
from dotenv import load_dotenv
from .models import app_db
from .routes import register_routes


load_dotenv()
VERSION = os.environ.get('VERSION')



def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    app_db.init_app(app)
    with app.app_context():
        from .util import register_filters
        register_filters(app)

        from .releases.routes import release_bp
        app.register_blueprint(release_bp)

        register_routes(app)

        @app.before_request
        def before_request():
            g.app_version = VERSION
        return app