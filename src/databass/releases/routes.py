from flask import Blueprint, render_template, request, redirect
from .. import db

release_bp = Blueprint(
    'release_bp', __name__,
    template_folder='templates'
)


@release_bp.route('/releases', methods=["GET"])
def releases():
    genres = sorted(db.get_distinct_col(db.Release, 'genre'))
    tags = sorted(db.get_distinct_col(db.Tag, 'name'))
    countries = sorted(db.get_distinct_col(db.Release, 'country'))
    all_labels = sorted(db.get_distinct_col(db.Label, 'name'))

    all_artists = sorted(db.get_distinct_col(db.Artist, 'name'))
    all_releases = sorted(db.get_distinct_col(db.Release, 'name'))
    data = {
        "genres": genres,
        "tags": tags,
        "countries": countries,
        "labels": all_labels,
        "releases": all_releases,
        "artists": all_artists
    }
    return render_template(
        'releases.html',
        data=data,
        active_page='releases'
    )

@release_bp.route('/release/<string:release_id>', methods=['GET'])
def release(release_id):
    # Displays all info related to a particular release
    release_data = db.exists('release', release_id)
    artist_data = db.exists('artist', release_data.artist_id)
    label_data = db.exists('label', release_data.label_id)
    existing_reviews = db.get_release_reviews(release_id)
    data = {"release": release_data,
            "artist": artist_data,
            "label": label_data,
            "reviews": existing_reviews}
    return render_template('release.html', data=data)


@release_bp.route('/edit/<string:release_id>', methods=['GET'])
def edit(release_id):
    release_data = db.exists(item_type='release', item_id=int(release_id))
    release_image = release_data.image[1:]
    label_id = release_data.label_id
    label_data = db.exists(item_type='label', item_id=label_id)
    artist_id = release_data.artist_id
    artist_data = db.exists(item_type='artist', item_id=artist_id)
    return render_template('edit.html',
                           release=release_data,
                           artist=artist_data,
                           label=label_data,
                           image=release_image)


@release_bp.route('/edit_release', methods=['POST'])
def edit_release():
        edit_data = request.form.to_dict()
        updated_release = db.construct_item('release', edit_data)
        db.update(updated_release)
        return redirect('/', 302)

@release_bp.route('/delete', methods=['POST', 'GET'])
def delete():
        data = request.get_json()
        deletion_id = data['id']
        deletion_type = data['type']
        print(f'Deleting {deletion_type} {deletion_id}')
        db.delete(item_type=deletion_type, item_id=deletion_id)
        return redirect('/', 302)

@release_bp.route('/add_review', methods=['POST'])
def add_review():
        review_data = request.form.to_dict()
        new_review = db.construct_item('review', review_data)
        db.insert(new_review)
        return redirect(request.referrer, 302)
