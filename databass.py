import flask
import api
import db
from uuid import uuid4
import os
from dotenv import load_dotenv
from flask_paginate import Pagination, get_page_parameter

# Application initialization
load_dotenv()
DB_FILENAME = os.getenv("DB_FILENAME")
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_FILENAME)
app = flask.Flask(__name__)
app.secret_key = uuid4().hex
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.static_folder = 'static'
db.db.init_app(app)


@app.before_request
def create_tables():
    db.db.create_all()


@app.route("/", methods=['GET'])
@app.route('/home', methods=['GET'])
def home():
    data = db.get_homepage_data()
    home_stats = db.get_stats()

    page = flask.request.args.get(
        get_page_parameter(),
        type=int,
        default=1
    )
    pagination = data.paginate(
        page=page,
        per_page=5,
        error_out=True
    )

    paged_data = pagination.items

    flask_pagination = Pagination(
        page=page,
        total=pagination.total,
        search=False,
        record_name='latest_releases'
    )

    return flask.render_template(
        'index.html',
        data=paged_data,
        stats=home_stats,
        pagination=flask_pagination,
        active_page='home'
    )


@app.route("/new")
def new():
    actions = ["search"]
    return flask.render_template("new.html", actions=actions, active_page='new')


@app.route("/search", methods=["POST"])
def search():
    search_data = flask.request.get_json()
    search_release = search_data["release"]
    search_artist = search_data["artist"]
    search_label = search_data["label"]

    data = api.pick_release(search_release, search_artist, search_label)

    return flask.render_template("search.html", data=data)


@app.route("/submit", methods=["POST"])
def submit():
    data = flask.request.form.to_dict()
    print(f'INFO: Request to submit release: {data}')
    release_id = data["release_id"]
    artist_id = data["artist_id"]
    label_id = data["label_id"]
    year = data["release_year"]
    genre = data["genre"]
    rating = data["rating"]
    tags = data["tags"]
    print(f"INFO: Fetching release info from API")
    release_data = api.get_release_data(release_id, year, genre, rating)
    print(f"INFO: API Response data: {release_data}")
    release_data["tags"] = tags
    if label_id:
        print(f"INFO: Checking if label with ID {label_id} exists in database")
        # check if label exists in database already, avoid some API calls
        # db.exists() returns an array; 1st element is True/False, 2nd is the entity ID
        label_exists = db.exists(mbid=label_id, item_type='label')
        if not label_exists[0]:
            print(f'INFO: No existing label found; inserting a new label')
            print(f'INFO: Fetching label info from API')
            # not in db already, get data and insert it
            label_data = api.get_label_data(label_id)
            print(f'INFO: API Response data: {label_data}')
            label_id = db.insert_label(label_data)
            # download image
            label_image_url = label_data["image"]
            print(f'INFO: Downloading label image from {label_image_url}')
            label_image_path = api.download_image(
                item_type='label',
                item_id=label_id,
                img_url=label_image_url
            )
            print(f'INFO: Label image downloaded to {label_image_path}')
            release_data["label_id"] = label_id
        else:
            print(f'INFO: Label already exists in database with ID {label_exists[1]}')
            release_data["label_id"] = label_exists[1]

    # check if artist exists in db already
    # db.exists() returns an array; 1st element is True/False, 2nd is the entity ID
    print(f"INFO: Checking if artist with ID {artist_id} exists in database")
    artist_exists = db.exists(
        mbid=artist_id,
        item_type='artist'
    )
    if not artist_exists[0]:
        # not in db
        print(f"INFO: No existing artist found; inserting a new artist")
        print(f'INFO: Fetching artist info from API')
        artist_data = api.get_artist_data(artist_id)
        print(f'INFO: API Response data: {artist_data}')
        artist_id = db.insert_artist(artist_data)
        # download image
        artist_image_url = artist_data["image"]
        print(f'INFO: Downloading artist image from {artist_image_url}')
        artist_image_path = api.download_image(
            item_type='artist',
            item_id=artist_id,
            img_url=artist_image_url
        )
        print(f'INFO: Artist image downloaded to {artist_image_path}')
        release_data["artist_id"] = artist_id
    else:
        print('INFO: Artist already exists in database.')
        release_data["artist_id"] = artist_exists[1]
    print(f"INFO: Inserting release into database")
    db_id = db.insert_release(release_data)    # db_id = primary key of release
    print(f'INFO: Release insertion successful with ID: {db_id}')
    # Download image after inserting release into db
    release_image_url = release_data["image"]
    print(f'INFO: Downloading release image from {release_image_url}')
    release_image_path = api.download_image(
        item_type='release',
        item_id=db_id,
        img_url=release_image_url)
    print(f'INFO: Image saved to {release_image_path}')
    return flask.redirect("/", code=302)


@app.route('/releases', methods=["GET"])
def releases():
    genres = db.distinct_entries(table=db.Release, column='genre')
    countries = db.distinct_entries(table=db.Release, column='country')
    all_labels = db.distinct_entries(table=db.Label, column='name')
    all_artists = db.distinct_entries(table=db.Artist, column='name')
    all_releases = db.distinct_entries(table=db.Release, column='title')
    data = {
        "genres": genres,
        "countries": countries,
        "labels": all_labels,
        "releases": all_releases,
        "artists": all_artists
    }
    return flask.render_template(
        'releases.html',
        data=data,
        active_page='releases'
    )


@app.route('/artists', methods=["GET"])
def artists():
    countries = db.distinct_entries(table=db.Artist, column='country')
    data = {"countries": countries}
    return flask.render_template('artists.html', data=data, active_page='artists')


@app.route('/labels', methods=["GET"])
def labels():
    countries = db.distinct_entries(table=db.Label, column='country')
    types = db.distinct_entries(table=db.Label, column='type')
    data = {"countries": countries, "types": types}
    return flask.render_template('labels.html', data=data, active_page='labels')


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


@app.route('/add-review', methods=['POST'])
def add_review():
    review_data = flask.request.form.to_dict()
    db.add_review(review_data)
    return flask.redirect('/', 302)


@app.route('/stats', methods=['GET'])
def stats():
    statistics = db.get_stats()
    return flask.render_template('stats.html', data=statistics, active_page='stats')


@app.route('/dynamic_search', methods=['POST'])
def dynamic_search():
    form_data = flask.request.get_json()
    search_results = db.dynamic_search(form_data)
    return flask.render_template('dynamic_search_results.html', data=search_results)


@app.route('/submit-manual', methods=['POST'])
def submit_manual():
    data = flask.request.form.to_dict()
    db.submit_manual(data)
    return flask.redirect('/', 302)


@app.template_filter('img_exists')
def img_exists(item_id, item_type, img_url):
    extension = api.get_image_type_from_url(img_url)
    print(f'INFO: Checking if image exists for {item_type} {item_id}{extension}')
    path = os.path.join(app.static_folder, 'img', item_type, f'{item_id}{extension}')
    print(f'INFO: Checking path: {path}')
    result = os.path.isfile(path)
    print(f'INFO: {result}')
    if result:
        url = flask.url_for('static', filename=f'img/{item_type}/{item_id}{extension}')
        print(f'INFO: Returning {url}')
        return url
    else:
        return result


def main():
    app.run(host='0.0.0.0', debug=True, port=8080)


if __name__ == '__main__':
    main()
