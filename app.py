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
    SELECT artist.name, release.title, release.rating FROM release
JOIN artist on artist.id = release.artist_id
ORDER BY release.listen_date DESC;
    """
    cur.execute(query)
    data = cur.fetchall()

    return flask.render_template("index.html", data=data)


@app.route("/new")
def new():
    actions = ["search"]
    return flask.render_template("new.html", actions=actions)


@app.route("/search", methods=["POST"])
def search():
    release = flask.request.form["release"]
    artist = flask.request.form["artist"]

    data = api.pick_release(release, artist)

    for i in data:
        print(i)
    return flask.render_template("search.html", data=data)


@app.route("/submit")
def submit():
    data = None
    return flask.redirect("/", code=302)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8080)