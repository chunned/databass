import flask
from flask import render_template, request, redirect, abort, flash
from flask_paginate import Pagination, get_page_parameter
from .api import Util, MusicBrainz, Discogs
from . import db
from .db import models
from .db.util import get_all_stats, handle_submit_data
from datetime import datetime

def register_routes(app):
    @app.route('/', methods=['GET'])
    @app.route('/home', methods=['GET'])
    def home() -> str:
        stats_data = get_all_stats()
        active_goals = models.Goal.get_incomplete()
        if active_goals is not None:
            goal_data = [process_goal_data(goal) for goal in active_goals]
        else:
            goal_data = []
        data = models.Release.home_data()

        page = request.args.get(
            get_page_parameter(),
            type=int,
            default=1
        )
        per_page = 5
        start, end = Util.get_page_range(per_page, page)

        paged_data = data[start:end]

        flask_pagination = Pagination(
            page=page,
            total=len(data),
            search=False,
            record_name='latest_releases'
        )

        return render_template(
            'index.html',
            data=paged_data,
            stats=stats_data,
            goals=goal_data,
            pagination=flask_pagination,
            active_page='home'
        )

    @app.route("/new")
    def new():
        actions = ["search"]
        return render_template("new.html", actions=actions, active_page='new')

    @app.route("/search", methods=["POST"])
    def search() -> str | flask.Response:
        # Initialize variables to None
        page = data_length = paged_data = release_data = per_page = None

        data = request.get_json()
        try:
            origin = data["referrer"]
        except KeyError:
            error = "Request referrer missing. You should only be coming to this page from /new or from the pagination buttons."
            flash(error)
            # TODO: move this error handling into errors/routes.py
            return redirect('/error')
        if origin == 'search':
            try:
                search_release = data["release"]
                search_artist = data["artist"]
                search_label = data["label"]
            except KeyError:
                error = "Request missing one of the expected keys"
                flash(error)
                # TODO: move this error handling into errors/routes.py
                return redirect('/error')
            if not search_release and not search_artist and not search_label:
                error = "ERROR: Search requires at least one search term"
                return error
            release_data = MusicBrainz.release_search(release=search_release,
                                                          artist=search_artist,
                                                          label=search_label)
            data_length = len(release_data)
            page = request.args.get(
                get_page_parameter(),
                type=int,
                default=1
            )
            per_page = 10
            start, end = Util.get_page_range(per_page, page)
            paged_data = release_data[start:end]
        elif origin == 'page_button':
            page = data["next_page"]
            per_page = data["per_page"]
            release_data = data["data"]
            data_length = len(release_data)
            start, end = Util.get_page_range(per_page, page)
            paged_data = release_data[start:end]

        if all(
            var is not None for var in [page, data_length, paged_data, release_data, per_page]
        ):
            # TODO: make generic pagination handler function
            flask_pagination = Pagination(
                page=page,
                total=data_length,
                search=False,
                record_name='search_results'
            )
            return render_template(
                "search/static.html",
                page=page,
                data=paged_data,
                pagination=flask_pagination,
                data_full=release_data,
                per_page=per_page
            )

    @app.route("/submit", methods=["POST"])
    def submit():
        data = request.form.to_dict()
        try:
            # Check if this is a manual submission (i.e. manually entered data, no results found from MusicBrainz)
            if data["manual_submit"] == "true":
                # try to grab optional fields
                try:
                    tags = data["tags"]
                except KeyError:
                    tags = ""
                try:
                    image = data["image"]
                except KeyError:
                    image = ""

                try:
                    runtime = int(data["runtime"])
                except KeyError:
                    runtime = 0

                try:
                    track_count = int(data["track_count"])
                except KeyError:
                    track_count = 0


                try:
                    country = data["country"]
                except KeyError:
                    country = "?"

                # TODO: add to frontend: runtime, track_count, country

                release_data = {
                    "name": data["name"],
                    "artist_name": data["artist"],
                    "label_name": data["label"],
                    "release_year": data["release_year"],
                    "genre": data["genre"],
                    "rating": data["rating"],
                    "tags": tags,
                    "image": image,
                    "listen_date": Util.today(),
                    "runtime": runtime,
                    "track_count": track_count,
                    "country": country
                }
                # TODO: improve manual submission; check Discogs for Artist/Label images, let user provide release image URL and auto-fetch it
                db.operations.submit_manual(release_data)
            elif data["manual_submit"] == "false":
                # Grab variables from request
                release_data = {
                    "release_group_mbid": data["release_group_id"],
                    "name": data["release_name"],
                    "mbid": data["release_mbid"],
                    "artist_name": data["artist"],
                    "artist_mbid": data["artist_mbid"],
                    "label_name": data["label"],
                    "label_mbid": data["label_mbid"],
                    "release_year": int(data["release_year"]),
                    "genre": data["genre"],
                    "rating": int(data["rating"]),
                    "track_count": data["track_count"],
                    "listen_date": Util.today(),
                    "country": data["country"],
                    "tags": data["tags"]
                }
                handle_submit_data(release_data)
        except KeyError:
            error = "Request missing one of the expected keys"
            flash(error)
            return redirect('/error')
        return redirect("/", code=302)

    @app.route('/stats', methods=['GET'])
    def stats():
        statistics = get_all_stats()
        return render_template('stats.html', data=statistics, active_page='stats')

    @app.route('/dynamic_search', methods=['POST'])
    def dynamic_search():
        # TODO: make a unique dynamic_search() in the routes.py for each entity (/release, /artist, /label); also simplify implementation

        data = request.get_json()
        origin = data["referrer"]
        del data["referrer"]
        if origin in ['release', 'artist', 'label']:
            if origin == 'release':
                search_data = db.models.Release.dynamic_search(data)
            elif origin == 'artist':
                search_data = db.models.Artist.dynamic_search(data)
            elif origin == 'label':
                search_data = db.models.Label.dynamic_search(data)
            else:
                raise ValueError("origin/referrer must be one of: release, artist, label")
            page = request.args.get(
                get_page_parameter(),
                type=int,
                default=1
            )
            search_type = search_data[0]
            search_results = search_data[1]
            # search_results is an array of SQLAlchemy objects; convert to array for use in JavaScript functions
            full_data = []
            for result in search_results:
                temp = result.__dict__
                if "_sa_instance_state" in temp:
                    del temp["_sa_instance_state"]
                for key in temp.keys():
                    if not temp[key]:
                        temp[key] = ""
                if search_type == 'release':
                    if "listen_date" in temp:
                        day = temp["listen_date"].date()
                        temp["listen_date"] = str(day)
                if search_type in ['label', 'artist']:
                    if "begin_date" in temp:
                        begin_date = temp["begin_date"]
                        if not begin_date:
                            begin_date = ""
                        else:
                            begin_date = begin_date.strftime('%Y-%m-%d')
                        temp["begin_date"] = begin_date
                    if "end_date" in temp:
                        end_date = temp["end_date"]
                        if not end_date:
                            end_date = ""
                        else:
                            end_date = end_date.strftime('%Y-%m-%d')
                        temp["end_date"] = end_date
                full_data.append(temp)
            data_length = len(search_results)
            per_page = 14
            start, end = Util.get_page_range(per_page, page)

            paged_data = full_data[start:end]

        elif origin == 'page_button':
            page = data["next_page"]
            per_page = data["per_page"]
            full_data = data["data"]
            start, end = Util.get_page_range(per_page, page)
            data_length = len(full_data)
            paged_data = full_data[start:end]
            for item in paged_data:
                # Iterate through paged_data to check for 'amp;' substrings, remove these substrings
                # Caused by '&' getting URL encoded
                for key in item:
                    if item[key] and isinstance(item[key], str) and 'amp;' in item[key]:
                        original_value = item[key]
                        new_value = original_value.replace('amp;', '')
                        item[key] = new_value
            search_type = data["search_type"]

        flask_pagination = Pagination(
            page=page,
            total=data_length,
            search=False,
            record_name="search_results"
        )
        return render_template(
            "search/dynamic.html",
            items=paged_data,
            pagination=flask_pagination,
            data_full=full_data,
            type=search_type,
            per_page=per_page
        )

    @app.route('/goals', methods=['GET'])
    def goals():
        if request.method != 'GET':
            abort(405)
        existing_goals = models.Goal.get_incomplete()
        if existing_goals is None:
            existing_goals = []
        data = {
            "today": Util.today(),
            "existing_goals": existing_goals
        }
        return render_template('goals.html', active_page='goals', data=data)

    @app.route('/add_goal', methods=['POST'])
    def add_goal():
        data = request.form.to_dict()
        if not data:
            error = "/add_goal received an empty payload"
            # TODO: move this error handling into errors/routes.py
            flash(error)
            return redirect('/error')
        try:
            goal = db.construct_item(model_name='goal', data_dict=data)
            if not goal:
                raise NameError("Construction of Goal object failed")
        except Exception as e:
            # TODO: move this error handling into errors/routes.py
            flash(str(e))
            return redirect('/error')

        db.insert(goal)
        return redirect('/goals', 302)

    # TODO: see if still needed
    @app.route('/stats_search', methods=['GET'])
    def stats_search():
        data = request.get_json()
        sort = data["sort"]
        metric = data["metric"]
        item_type = data["item_type"]
        item_property = data["item_property"]
        stats.search(sort=sort,
                     metric=metric,
                     item_type=item_type,
                     item_property=item_property)

    # TODO: see if still needed
    @app.route('/imgupdate/<item_type>/<item_id>')
    def imgupdate(item_type, item_id):
        print(f'Checking: {item_type} {item_id}')
        item_id = int(item_id)
        if item_type == 'release':
            item = models.Release.exists_by_id(item_id)
        elif item_type == 'artist':
            item = models.Artist.exists_by_id(item_id)
        elif item_type == 'label':
            item = models.Label.exists_by_id(item_id)
        else:
            raise ValueError(f"Unexpected item_type: {item_type}")
        try:
            img_path = '.' + Util.img_exists(item_id=item_id, item_type=item_type)
            print(f'Local image already exists: {img_path}')
        except TypeError:
            print('Local image not found, attempting to grab from external sources.')
            # No local image exists, grab it
            if item_type == 'release':
                release_name = item.name
                release_artist = models.Artist.exists_by_id(item.artist_id)
                artist_name = release_artist.name
                img_path = Util.get_image(
                    item_type=item_type,
                    item_id=item_id,
                    mbid=item.mbid,
                    release_name=release_name,
                    artist_name=artist_name
                )
            elif item_type == 'artist':
                artist_name = item.name
                img_path = Util.get_image(
                    item_type=item_type,
                    item_id=item_id,
                    mbid=item.mbid,
                    artist_name=artist_name
                )
            elif item_type == 'label':
                label_name = item.name
                img_path = Util.get_image(
                    item_type=item_type,
                    item_id=item_id,
                    mbid=item.mbid,
                    label_name=label_name
                )
        finally:
            if item.image != img_path:
                item.image = img_path
                print(f'Updating database entry: {item_type}.image => {img_path}')
                db.update(item)
            # Define the mappings for the order of items. All releases are fixed 1 by 1, then artists, then labels
            next_type = {
                'release': 'artist',
                'artist': 'label',
                'label': None
            }
            next_item = db.util.next_item(item_type=item_type, prev_id=item_id)
            if next_item:
                return redirect(f'/imgupdate/{item_type}/{next_item.id}')
            else:
                # No next item; move onto next item type
                next_item = next_type.get(item_type)
                if next_item:
                    return redirect(f'/imgupdate/{next_item}/0')
                else:
                    # Complete, redirect to home
                    return redirect('/', code=302)

    # TODO: see if still needed
    @app.route('/fix_images')
    def fix_images():
        print('Fixing images.')
        # Starts the imgupdate process; imgupdate() will recursively call itself and update all images 1 by 1
        return redirect('/imgupdate/release/1')

    # TODO: see if still needed
    @app.route('/backup', methods=['GET'])
    def backup():
        bkp()
        return redirect('/', code=302)


def process_goal_data(goal: models.Goal):
    """
    Processes the data for a given goal, calculating the current progress, remaining amount, and daily target.

    Args:
        goal (models.Goal): The goal object to process.

    Returns:
        dict: A dictionary containing the following keys:
            - start_date (datetime): The start date of the goal.
            - end_goal (datetime): The end date of the goal.
            - type (str): The type of the goal.
            - amount (int): The total amount of the goal.
            - progress (float): The current progress of the goal as a percentage.
            - target (float): The daily target amount needed to reach the goal.
            - current (int): The current amount achieved for the goal.
    """
    current = goal.new_releases_since_start_date
    remaining = goal.amount - current
    days_left = (goal.end_goal - datetime.today()).days
    try:
        target = round((remaining / days_left), 2)
    except ZeroDivisionError:
        target = 0
    return {
        "start_date": goal.start_date,
        "end_goal": goal.end_goal,
        "type": goal.type,
        "amount": goal.amount,
        "progress": round((current / goal.amount) * 100),
        "target": target,
        "current": current
    }
