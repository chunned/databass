import flask
import db_2
import os
from dotenv import load_dotenv


db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alchemy.db')

app = flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
db_2.db.init_app(app)


@app.before_request
def create_tables():
    db_2.db.create_all()


if __name__ == "__main__":
    #app.run(host="0.0.0.0", debug=True, port=8080)

    ## TESTING
    release_data = {
        "mbid": "test-mbid",
        "artist_id": "1",
        "label_id": "1",
        "title": "Test Release",
        "release_year": "2022",
        "runtime": "60",
        "rating": "5",
        "listen_date": "2023-01-01",
        "track_count": "10",
        "country": "US",
        "art": "test-art",
        "genre": "Rock",
        "tags": "test-tag"
    }
    with app.app_context():
        db_2.insert_release(release_data)