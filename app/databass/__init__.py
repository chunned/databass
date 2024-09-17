from flask import Flask, g
import os
from dotenv import load_dotenv
from .models import db

load_dotenv()
VERSION = os.environ.get('VERSION')



def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)
    with app.app_context():
        from .util import register_filters
        register_filters(app)

        from .home import routes
        app.register_blueprint(home.routes.home_bp)

        @app.before_request
        def before_request():
            g.app_version = VERSION
        return app