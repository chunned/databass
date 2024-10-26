from flask import Blueprint, render_template, request, redirect, flash
from flask_paginate import Pagination, get_page_parameter
from .. import db
from ..db import models
from ..api import Util

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
    if not release_data:
        error = f"No release with id {release_id} found."
        flash(error)
        return redirect('/error', code=302)
    artist_data = models.Artist.exists_by_id(release_data.artist_id)
    label_data = models.Label.exists_by_id(release_data.label_id)
    existing_reviews = models.Release.get_reviews(int(release_id))
    data = {"release": release_data,
            "artist": artist_data,
            "label": label_data,
            "reviews": existing_reviews}
    return render_template('release.html', data=data)

@release_bp.route('/release/<string:release_id>/edit', methods=['GET', 'POST'])
def edit_release(release_id):
    # Check if release exists
    release_data = models.Release.exists_by_id(int(release_id))
    if not release_data:
        error = f"No release with id {release_id} found."
        flash(error)
        return redirect('/error', code=302)
    # Handle actual request
    if request.method == 'GET':
        release_image = release_data.image[1:]
        label_data = models.Label.exists_by_id(release_data.label_id)
        artist_data = models.Artist.exists_by_id(release_data.artist_id)
        return render_template('edit.html',
                               release=release_data,
                               artist=artist_data,
                               label=label_data,
                               image=release_image)
    elif request.method == 'POST':
        edit_data = request.form.to_dict()
        image = edit_data["image"]
        if "http" and "://" in image:
            # If image is a URL, we need to download it
            # TODO: move this into dedicated function when Util.get_image is rewritten
            import requests
            from dotenv import load_dotenv
            from os import getenv
            load_dotenv()
            VERSION = getenv("VERSION")

            response = requests.get(image, headers={
                "Accept": "application/json",
                "User-Agent": f"databass/{VERSION} (https://github.com/chunned/databass)"
            })
            if response:
                ext = Util.get_image_type_from_url(image)
                base_path = './databass/static/img'
                image_filepath = base_path + '/release/' + edit_data["id"] + ext
                with open(image_filepath, 'wb') as img_file:
                    img_file.write(response.content)

                edit_data["image"] = image_filepath.replace('databass/', '')

        updated_release = db.construct_item('release', edit_data)
        # construct_item() will produce a unique ID primary key, so we need to set it to the original one for update() to work
        try:
            updated_release.id = edit_data['id']
        except KeyError:
            error = f"Edit data missing ID key, unable to update an existing entry without ID."
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
    else:
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
    if "text" not in review_data.keys() or "id" not in review_data.keys():
        error = "Request missing one of the required variables: text, id (release id)"
        flash(error)
        return redirect("/error", code=302)
    # Perform deletion
    new_review = db.construct_item('review', review_data)
    db.insert(new_review)
    return redirect(request.referrer, 302)

@release_bp.route('/release_search', methods=['POST'])
def release_search():
    data = request.get_json()
    search_results = models.Release.dynamic_search(data)
    # TODO: extract pagination functionality from all routes
    # page = request.args.get(
    #     get_page_parameter(),
    #     type=int,
    #     default=1
    # )
    # full_data = []
    return render_template('release_search.html', data=search_results)
