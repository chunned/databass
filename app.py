import flask
import api
import db


app = flask.Flask(__name__)
db_file = "music.db"


@app.route("/")
def home():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    query = """
    SELECT artist.name, release.title, release.rating, release.listen_date, release.genre, release.art FROM release
JOIN artist on artist.id = release.artist_id
ORDER BY release.listen_date DESC
LIMIT 10;
    """
    cur.execute(query)
    data = cur.fetchall()
    stats = db.get_stats(cur, con)
    return flask.render_template("index.html", data=data, stats=stats, active_page='home')


@app.route("/new")
def new():
    actions = ["search"]
    return flask.render_template("new.html", actions=actions, active_page='new')


@app.route("/search", methods=["POST"])
def search():
    release = flask.request.form["release"]
    artist = flask.request.form["artist"]
    rating = flask.request.form["rating"]
    year = flask.request.form["year"]
    genre = flask.request.form["genre"]

    data = api.pick_release(release, artist, rating, year, genre)

    return flask.render_template("search.html", data=data)


@app.route("/submit", methods=["POST"])
def submit():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    data = eval(flask.request.form.get('selected_item'))
    release = data["release"]
    artist = data["artist"]
    label = data["label"]
    year = data["release_date"]
    genre = data["genre"]
    rating = data["rating"]

    release_data = api.get_release_data(release["id"], year, genre, rating)
    if label["mbid"]:
        label_id = db.insert_label(cur, con, label)
        release_data["label_id"] = label_id

    artist_id = db.insert_artist(cur, con, artist)
    release_data["artist_id"] = artist_id

    db.insert_release(cur, con, release_data)

    return flask.redirect("/", code=302)


@app.route('/releases', methods=["GET"])
def releases():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)
    cur.execute("SELECT * FROM release")
    data = cur.fetchall()

    return flask.render_template('releases.html', data=data)


@app.route('/artists', methods=["GET"])
def artists():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    cur.execute("SELECT * FROM artist")
    data = cur.fetchall()

    return flask.render_template('artists.html', data=data)


@app.route('/labels', methods=["GET"])
def labels():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)
    cur.execute("SELECT * FROM label")
    data = cur.fetchall()

    return flask.render_template('labels.html', data=data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)