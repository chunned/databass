import flask
import api
import db
from uuid import uuid4
import os
from dotenv import load_dotenv

# Application initialization
load_dotenv()
DB_FILENAME = os.getenv("DB_FILENAME")
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
app = flask.Flask(__name__)
app.secret_key = uuid4().hex
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
db.db.init_app(app)


@app.before_request
def create_tables():
    db.db.create_all()


@app.route("/")
def home():
    data = db.get_homepage_data()
    home_stats = db.get_stats()
    return flask.render_template("index.html", data=data, stats=home_stats, active_page='home')


@app.route("/new")
def new():
    actions = ["search"]
    return flask.render_template("new.html", actions=actions, active_page='new')


@app.route("/search", methods=["POST"])
def search():
    search_release = flask.request.form["release"]
    search_artist = flask.request.form["artist"]

    data = api.pick_release(search_release, search_artist)

    return flask.render_template("search.html", data=data)


@app.route("/submit", methods=["POST"])
def submit():
    data = flask.request.form.to_dict()
    release_id = data["release_id"]
    artist_id = data["artist_id"]
    label_id = data["label_id"]
    year = data["release_year"]
    genre = data["genre"]
    rating = data["rating"]
    tags = data["tags"]

    release_data = api.get_release_data(release_id, year, genre, rating)
    release_data["tags"] = tags
    if label_id:
        # check if label exists in database already, avoid some API calls
        # db.exists() returns an array; 1st element is True/False, 2nd is the entity ID
        label_exists = db.exists(mbid=label_id, item_type='label')
        if not label_exists[0]:
            # not in db already, get data and insert it
            label_data = api.get_label_data(label_id)
            label_id = db.insert_label(label_data)
            release_data["label_id"] = label_id
        else:
            print('INFO: Label already exists in database.')
            release_data["label_id"] = label_exists[1]

    # check if artist exists in db already
    # db.exists() returns an array; 1st element is True/False, 2nd is the entity ID
    artist_exists = db.exists(mbid=artist_id, item_type='artist')
    if not artist_exists[0]:
        # not in db
        artist_data = api.get_artist_data(artist_id)
        artist_id = db.insert_artist(artist_data)
        release_data["artist_id"] = artist_id
    else:
        print('INFO: Artist already exists in database.')
        release_data["artist_id"] = artist_exists[1]

    db.insert_release(release_data)

    return flask.redirect("/", code=302)


@app.route('/releases', methods=["GET"])
def releases():
    release_data = db.get_items('releases')
    return flask.render_template('releases.html', data=release_data, active_page='releases')


@app.route('/artists', methods=["GET"])
def artists():
    artist_data = db.get_items('artists')
    return flask.render_template('artists.html', data=artist_data, active_page='artists')


@app.route('/labels', methods=["GET"])
def labels():
    label_data = db.get_items('labels')
    return flask.render_template('labels.html', data=label_data, active_page='labels')


@app.route('/release/<string:release_id>', methods=['GET'])
def release(release_id):
    # Displays all info related to a particular release
    release_data = db.get_item(item_type='release', item_id=release_id)
    return flask.render_template('release.html', data=release_data)


@app.route('/artist/<string:artist_id>', methods=['GET'])
def artist(artist_id):
    # Displays all info related to a particular artist
    artist_data = db.get_item(item_type='artist', item_id=artist_id)
    return flask.render_template('artist.html', data=artist_data)


@app.route('/label/<string:label_id>', methods=['GET'])
def label(label_id):
    label_data = db.get_item(item_type='label', item_id=label_id)
    return flask.render_template('label.html', data=label_data)


@app.route('/charts', methods=['GET'])
def charts():
    # Not implemented
    # con = db.create_connection('music.db')
    # cur = db.create_cursor(con)
    #
    # query = "SELECT rating FROM release"
    # cur.execute(query)
    # data = cur.fetchall()
    #
    # data = [n[0] for n in data]
    # return flask.render_template('charts.html', data=data)
    return flask.redirect('/', 302)


@app.route('/edit/<string:release_id>', methods=['GET'])
def edit(release_id):
    data = db.get_item('release', release_id)
    return flask.render_template('edit.html', data=data)


@app.route('/edit-release', methods=['POST'])
def edit_release():
    edit_data = flask.request.form.to_dict()
    db.update_release(edit_data)

    return flask.redirect('/', 302)


@app.route('/delete', methods=['POST', 'GET'])
def delete():
    deletion_id = flask.request.get_json()['id']
    db.delete_item('release', deletion_id)
    return flask.redirect('/', 302)


@app.route('/stats', methods=['GET'])
def stats():
    statistics = db.get_stats()
    return flask.render_template('stats.html', data=statistics, active_page='stats')


def main():
    app.run(host='0.0.0.0', debug=True, port=8080)


if __name__ == '__main__':
    main()
