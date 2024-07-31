import flask
import api
import db
from uuid import uuid4
from flask_sqlalchemy import SLQAlchemy


app = flask.Flask(__name__)
app.secret_key = uuid4().hex
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///music.db'

db_file = 'music.db'

con = db.create_connection(db_file)
cur = db.create_cursor(con)
db.create_tables(cur)


@app.route("/")
def home():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    query = """
    SELECT artist.name, release.title, release.rating, release.listen_date, release.genre, release.art, 
    release.mbid, artist.mbid, release.tags 
    FROM release
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

    data = api.pick_release(release, artist)

    return flask.render_template("search.html", data=data)


@app.route("/submit", methods=["POST"])
def submit():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    # data = eval(flask.request.form.get('selected_item'))
    data = flask.request.form.to_dict()
    release = data["release"]
    release_id = data["release_id"]
    artist = data["artist"]
    artist_id = data["artist_id"]
    label = data["label"]
    label_id = data["label_id"]
    year = data["release_date"]
    genre = data["genre"]
    rating = data["rating"]
    tags = data["tags"]

    release_data = api.get_release_data(release_id, year, genre, rating)
    release_data["tags"] = tags
    if label_id:
        # check if label exists in database already, avoid some API calls
        cur.execute("SELECT * FROM label WHERE mbid = ?", (label_id,))
        res = cur.fetchone()
        if not res:
            # not in db already, get data and insert it
            label_data = api.get_label_data(label_id)
            label_id = db.insert_label(cur, con, label_data)
            release_data["label_id"] = label_id
        else:
            release_data["label_id"] = res[0]

    # check if artist exists in db already
    cur.execute("SELECT * FROM artist WHERE mbid = ?", (artist_id,))
    res = cur.fetchone()
    if not res:
        # not in db
        artist_data = api.get_artist_data(artist_id)
        artist_id = db.insert_artist(cur, con, artist_data)
        release_data["artist_id"] = artist_id
    else:
        release_data["artist_id"] = res[0]

    db.insert_release(cur, con, release_data)

    return flask.redirect("/", code=302)


@app.route('/releases', methods=["GET"])
def releases():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)
    cur.execute("SELECT * FROM release LIMIT 25")
    data = cur.fetchall()

    return flask.render_template('releases.html', data=data, active_page='releases')


@app.route('/artists', methods=["GET"])
def artists():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    cur.execute("SELECT * FROM artist LIMIT 25")
    data = cur.fetchall()

    return flask.render_template('artists.html', data=data, active_page='artists')


@app.route('/labels', methods=["GET"])
def labels():
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)
    cur.execute("SELECT * FROM label ORDER BY id DESC LIMIT 25")
    data = cur.fetchall()

    return flask.render_template('labels.html', data=data, active_page='labels')


@app.route('/release/<string:release_id>', methods=['GET'])
def release(release_id):
    # displays all info related to a particular release
    con = db.create_connection(db_file)
    cur = db.create_cursor(con)

    query = "SELECT * FROM release WHERE release.mbid = ?"
    cur.execute(query, (release_id,))
    release_data = cur.fetchall()

    query = "SELECT * FROM artist WHERE artist.id = ?"
    cur.execute(query, (release_data[0][2],))
    artist_data = cur.fetchall()

    query = "SELECT * FROM label WHERE label.id = ?"
    cur.execute(query, (release_data[0][3],))
    label_data = cur.fetchall()

    data = [release_data[0], artist_data[0], label_data[0]]
    return flask.render_template('release.html', data=data)


@app.route('/artist/<string:artist_id>', methods=['GET'])
def artist(artist_id):
    con = db.create_connection('music.db')
    cur = db.create_cursor(con)

    query = "SELECT * FROM artist WHERE artist.mbid = ?"
    cur.execute(query, (artist_id,))

    artist_data = cur.fetchall()
    print(artist_data)
    query = """
    SELECT * FROM label
    JOIN release ON label.id = release.label_id
    JOIN artist ON artist.id = release.artist_id
    WHERE artist.id = ?
    """
    cur.execute(query, (artist_data[0][0],))
    release_data = cur.fetchall()

    data = [artist_data[0], release_data]
    return flask.render_template('artist.html', data=data)


@app.route('/label/<string:label_id>', methods=['GET'])
def label(label_id):
    con = db.create_connection('music.db')
    cur = db.create_cursor(con)

    query = "SELECT * FROM label WHERE label.mbid = ?"
    cur.execute(query, (label_id,))
    label_data = cur.fetchall()

    query = "SELECT * FROM release JOIN artist on artist.id = release.artist_id WHERE release.label_id = ?"
    cur.execute(query, (label_data[0][0],))
    release_data = cur.fetchall()

    data = [label_data[0], release_data]

    return flask.render_template('label.html', data=data)


@app.route('/charts', methods=['GET'])
def charts():
    con = db.create_connection('music.db')
    cur = db.create_cursor(con)

    query = "SELECT rating FROM release"
    cur.execute(query)
    data = cur.fetchall()

    data = [n[0] for n in data]
    return flask.render_template('charts.html', data=data)


@app.route('/edit/<string:release_id>', methods=['GET'])
def edit(release_id):
    con = db.create_connection('music.db')
    cur = db.create_cursor(con)

    query = "SELECT * FROM release WHERE id = ?"
    cur.execute(query, (release_id,))

    data = cur.fetchone()
    return flask.render_template('edit.html', data=data)


@app.route('/edit-release', methods=['POST'])
def edit_release():
    data = flask.request.form.to_dict()

    con = db.create_connection('music.db')
    cur = db.create_cursor(con)

    cur.execute(
        """
        UPDATE release
        SET title = :title,
            release_date = :year,
            rating = :rating,
            genre = :genre
        WHERE id = :id
        """,
        data
    )
    con.commit()
    return flask.redirect("/", code=302)


@app.route('/stats', methods=['GET'])
def stats():
    con = db.create_connection('music.db')
    cur = db.create_cursor(con)

    stats = db.get_stats(cur, con)
    return flask.render_template('stats.html', data=stats, active_page='stats')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)