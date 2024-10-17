from flask import Blueprint, render_template, request
from .. import db

artist_bp = Blueprint(
    'artist_bp', __name__,
    template_folder='templates'
)


@artist_bp.route('/artist/<string:artist_id>', methods=['GET'])
def artist(artist_id):
    # Displays all info related to a particular artist
    artist_data = db.exists(item_type='artist', item_id=artist_id)
    artist_releases = db.get_artist_releases(artist_id)
    data = {"artist": artist_data, "releases": artist_releases}
    return render_template('artist.html', data=data)

@artist_bp.route('/artists', methods=["GET"])
def artists():
    countries = db.get_distinct_col(db.Artist, 'country')
    data = {"countries": countries}
    return render_template('artists.html', data=data, active_page='artists')

@artist_bp.route('/artist/<string:artist_id>', methods=['GET', 'POST'])
def edit_artist(artist_id):
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass
