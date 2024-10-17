from flask import Blueprint, render_template, request, flash, redirect
from ..db.models import Artist

artist_bp = Blueprint(
    'artist_bp', __name__,
    template_folder='templates'
)


@artist_bp.route('/artist/<string:artist_id>', methods=['GET'])
def artist(artist_id):
    # Displays all info related to a particular artist
    artist_data = Artist.exists_by_id(item_id=artist_id)
    if not artist_data:
        error = f"No release with id {artist_id} found."
        flash(error)
        return redirect('/error', code=302)

    artist_releases = Artist.get_releases(artist_id)
    data = {"artist": artist_data, "releases": artist_releases}
    return render_template('artist.html', data=data)

@artist_bp.route('/artists', methods=["GET"])
def artists():
    countries = Artist.get_distinct_column_values('country')
    data = {"countries": countries}
    return render_template('artists.html', data=data, active_page='artists')

@artist_bp.route('/artist/<string:artist_id>', methods=['GET', 'POST'])
def edit_artist(artist_id):
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass
