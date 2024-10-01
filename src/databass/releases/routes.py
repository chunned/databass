from flask import Blueprint, render_template, request, redirect
from .. import db
from ..db import models

release_bp = Blueprint(
    'release_bp', __name__,
    template_folder='templates'
)


@release_bp.route('/releases', methods=["GET"])
def releases():
    genres = sorted(models.Release.get_distinct_column_values('genre'))
    tags = sorted(models.Tag.get_distinct_column_values('name'))
    countries = sorted(models.Release.get_distinct_column_values('country'))
    all_labels = sorted(models.Label.get_distinct_column_values('name'))
    all_artists = sorted(models.Artist.get_distinct_column_values('name'))
    all_releases = sorted(models.Release.get_distinct_column_values('name'))
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
    release_data = models.Release.exists_by_id(release_id)
    artist_data = models.Artist.exists_by_id(release_data.artist_id)
    label_data = models.Label.exists_by_id(release_data.label_id)
    existing_reviews = models.Release.get_reviews(release_id)
    data = {"release": release_data,
            "artist": artist_data,
            "label": label_data,
            "reviews": existing_reviews}
    return render_template('release.html', data=data)


@release_bp.route('/edit/<string:release_id>', methods=['GET'])
def edit(release_id):
    release_data = models.Release.exists_by_id(int(release_id))
    release_image = release_data.image[1:]
    label_data = models.Label.exists_by_id(release_data.label_id)
    artist_data = models.Artist.exists_by_id(release_data.artist_id)
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
