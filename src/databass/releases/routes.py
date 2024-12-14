from flask import Blueprint, render_template, request, redirect, flash
from .. import db
from ..db import models
from ..api import Util

release_bp = Blueprint(
    'release_bp', __name__,
    template_folder='templates'
)

@release_bp.route('/release/<string:release_id>', methods=['GET'])
def release(release_id):
    # Displays all info related to a particular release
    release_data = models.Release.exists_by_id(release_id)
    if not release_data:
        error = f"No release with id {release_id} found."
        flash(error)
        return redirect('/error', code=302)
    artist_data = models.Artist.exists_by_id(release_data.artist_id)
    label_data = models.Label.exists_by_id(release_data.label_id)
    existing_reviews = models.Release.get_reviews(int(release_id))
    label = models.Label.exists_by_id(release_data.label_id)
    if label.name == '[NONE]':
        label_releases = []
    else:
        label_releases = models.Label.get_releases(label.id)

    artist = models.Artist.exists_by_id(release_data.artist_id)
    if artist.name in ('Various Artists', '[NONE]'):
        artist_releases = []
    else:
        artist_releases = models.Artist.get_releases(release_data.artist_id)

    data = {
        "release": release_data,
        "artist": artist_data,
        "label": label_data,
        "reviews": existing_reviews,
        "label_releases": label_releases,
        "artist_releases": artist_releases
    }
    return render_template('release.html', data=data)


@release_bp.route('/release/<string:release_id>/edit', methods=['GET', 'POST'])
def edit(release_id):
    # Check if release exists
    release_data = models.Release.exists_by_id(int(release_id))
    if not release_data:
        error = f"No release with id {release_id} found."
        flash(error)
        return redirect('/error', code=302)

    if request.method == 'GET':
        release_image = release_data.image[1:]
        label_data = models.Label.exists_by_id(release_data.label_id)
        artist_data = models.Artist.exists_by_id(release_data.artist_id)
        countries = sorted(models.Release.get_distinct_column_values('country'))
        return render_template(
            'edit.html',
            release=release_data,
            artist=artist_data,
            label=label_data,
            image=release_image,
            countries=countries
        )
    if request.method == 'POST':
        edit_data = request.form.to_dict()
        submit_data = {}

        # image
        try:
            if edit_data["image"]:
                image = edit_data["image"]
                if "http" and "://" in image:
                    # If image is a URL, download it
                    new_image = Util.get_image(
                        item_type='release',
                        item_id=release_id,
                        url=image
                    )
                    submit_data["image"] = new_image
                else:
                    print("Image not a URL. Skipping.")
        except KeyError:
            pass

        # release year
        try:
            year = edit_data["release_year"]
            if year:
                submit_data["release_year"] = year
        except KeyError:
            pass

        # listen date
        try:
            listen_date = edit_data["listen_date"]
            if listen_date:
                from datetime import datetime
                submit_data["listen_date"] = datetime.strptime(listen_date, "%Y-%m-%d")
        except KeyError:
            pass

        # rating
        try:
            rating = edit_data["rating"]
            if rating:
                submit_data["rating"] = rating
        except KeyError:
            pass

        # genre
        try:
            genre = edit_data["genre"]
            if genre:
                submit_data["genre"] = genre
        except KeyError:
            pass

        # country
        try:
            country = edit_data["country"]
            if country:
                submit_data["country"] = country
        except KeyError:
            pass

        updated_release = db.construct_item('release', submit_data)
        # construct_item() will produce a unique ID primary key, so we need to set it to the original one for update() to work
        try:
            updated_release.id = release_id
            # grab the other release so we can inject the data that doesn't change
            old_release = models.Release.exists_by_id(release_id)
            updated_release.artist_id = old_release.artist_id
            updated_release.label_id = old_release.label_id
            updated_release.runtime = old_release.runtime
            updated_release.track_count = old_release.track_count
            updated_release.tags = old_release.tags # TODO: allow editing for tags

        except KeyError:
            error = "Edit data missing ID, unable to update an existing entry without ID."
            flash(error)
            return redirect('/error', code=302)
        db.update(updated_release)
        return redirect('/', 302)



@release_bp.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    try:
        deletion_id = data['id']
        deletion_type = data['type']
    except KeyError:
        error = "Deletion request missing one of the required variables (ID or type)"
        flash(error)
        return redirect('/error', code=302)

    if not models.Release.exists_by_id(deletion_id):
        error = f"No release with id {deletion_id} found."
        flash(error)
        return redirect('/error', code=302)
    print(f'Deleting {deletion_type} {deletion_id}')
    db.delete(item_type=deletion_type, item_id=deletion_id)
    return redirect('/', 302)

@release_bp.route('/release/<string:release_id>/add_review', methods=['POST'])
def add_review(release_id):
    # Make sure release exists before doing anything
    if not models.Release.exists_by_id(int(release_id)):
        error = f"No release with ID {release_id} found"
        flash(error)
        return redirect("/error", code=302)
    # Ensure request has required data
    review_data = request.form.to_dict()
    if "text" not in review_data.keys():
        error = "Request missing one of the required variables: text"
        flash(error)
        return redirect("/error", code=302)
    # Perform deletion
    new_review = db.construct_item('review', review_data)
    db.insert(new_review)
    return redirect(request.referrer, 302)

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

@release_bp.route('/release_search', methods=['POST'])
def release_search():
    from ..pagination import Pager
    data = request.get_json()
    search_results = models.Release.dynamic_search(data)

    page = Pager.get_page_param(request)
    paged_data, flask_pagination = Pager.paginate(
        per_page=15,
        current_page=page,
        data=search_results
    )

    return render_template(
        'release_search.html',
        data=paged_data,
        data_full=search_results,
        pagination=flask_pagination
    )
