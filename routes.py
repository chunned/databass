from flask import render_template, request, redirect
from flask_paginate import Pagination, get_page_parameter
import api2
import util
from stats import get_all as get_stats, get_homepage_releases as get_releases
import db


def register_routes(app):
    @app.route('/', methods=['GET'])
    @app.route('/home', methods=['GET'])
    def home():
        stats_data = get_stats()
        active_goals = db.get_incomplete_goals()
        goal_data = []
        for goal in active_goals:
            start_date = goal.start_date
            end_goal = goal.end_goal
            goal_type = goal.type
            amount = goal.amount

            current = goal.new_releases_since_start_date
            remaining = amount - current
            days_left = (end_goal - start_date).days
            progress = round((current / amount) * 100)
            target = remaining / days_left
            goal_data.append({
                "start_date": start_date,
                "end_goal": end_goal,
                "type": goal_type,
                "amount": amount,
                "progress": progress,
                "target": target,
                "current": current
            })

        data = get_releases()
        page = request.args.get(
            get_page_parameter(),
            type=int,
            default=1
        )
        per_page = 5
        start, end = util.get_page_range(per_page, page)
        
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
    def search():
        data = request.get_json()
        origin = data["referrer"]
        if origin == 'search':
            search_release = data["release"]
            search_artist = data["artist"]
            search_label = data["label"]
            #release_data = api.pick_release(search_release, search_artist, search_label)
            release_data = api2.search(release=search_release, artist=search_artist, label=search_label)
            data_length = len(release_data)
            page = request.args.get(
                get_page_parameter(),
                type=int,
                default=1
            )
            per_page = 10
            start, end = util.get_page_range(per_page, page)
            paged_data = release_data[start:end]
        elif origin == 'page_button':
            page = data["next_page"]
            per_page = data["per_page"]
            release_data = data["data"]
            data_length = len(release_data)
            start, end = util.get_page_range(per_page, page)
            paged_data = release_data[start:end]

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
        print(f'INFO: Request to submit release: {data}')
        release_mbid = data["release_mbid"]
        artist_mbid = data["artist_mbid"]
        label_mbid = data["label_mbid"]
        year = data["release_year"]
        genre = data["genre"]
        rating = data["rating"]
        tags = data["tags"]
        print(f"INFO: Fetching release info from API")
        release_data = api.get_release_data(release_mbid, year, genre, rating)
        print(f"INFO: API Response data: {release_data}")
        if label_mbid:
            print(f"INFO: Checking if label with ID {label_mbid} exists in database")
            # check if label exists in database already, avoid some API calls
            label_exists = db.exists(item_type='label', mbid=label_mbid)
            if not label_exists:
                print(f'INFO: No existing label found; inserting a new label')
                print(f'INFO: Fetching label info from API')
                # not in db already, get data and insert it
                label_data = api.get_label_data(label_mbid)
                print(f'INFO: API Response data: {label_data}')
                # Turn date strings into datetime.date objects
                begin_date = util.to_date('begin', label_data['begin_date'])
                label_data['begin_date'] = begin_date
                end_date = util.to_date('end', label_data['end_date'])
                label_data['end_date'] = end_date
                new_label = db.construct_item('label', label_data)
                label_id = db.insert(new_label)
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
                print(f'INFO: Label already exists in database with ID {label_exists[0].id}')
                release_data["label_id"] = label_exists[0].id

        # check if artist exists in db already
        if artist_mbid:
            print(f"INFO: Checking if artist with ID {artist_mbid} exists in database")
            artist_exists = db.exists(item_type='artist', mbid=artist_mbid)
            if not artist_exists:
                # not in db
                print(f"INFO: No existing artist found; inserting a new artist")
                print(f'INFO: Fetching artist info from API')
                artist_data = api.get_artist_data(artist_mbid)
                print(f'INFO: API Response data: {artist_data}')
                # Turn date strings into datetime.date objects
                begin_date = util.to_date('begin', artist_data['begin_date'])
                artist_data['begin_date'] = begin_date
                end_date = util.to_date('end', artist_data['end_date'])
                artist_data['end_date'] = end_date
                new_artist = db.construct_item('artist', artist_data)
                artist_id = db.insert(new_artist)
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
                print(f'INFO: Artist already exists in database with ID {artist_exists[0].id}')
                release_data["artist_id"] = artist_exists[0].id

        print(f"INFO: Inserting release into database")
        new_release = db.construct_item('release', release_data)
        release_id = db.insert(new_release)
        print(f'INFO: Release insertion successful with ID: {release_id}')
        print('Inserting tags')
        print(tags)
        for tag in tags.split(','):
            tag_data = {"name": tag, "release_id": release_id}
            tag_obj = db.construct_item('tags', tag_data)
            db.insert(tag_obj)
        # Download image after inserting release into db
        release_image_url = release_data["image"]
        print(f'INFO: Downloading release image from {release_image_url}')
        release_image_path = api.download_image(
            item_type='release',
            item_id=release_id,
            img_url=release_image_url)
        print(f'INFO: Image saved to {release_image_path}')
        print('INFO: Checking active goals')
        goals = db.get_incomplete_goals()
        for goal in goals:
            goal.check_and_update_goal()
            if goal.end_actual:
                print(f'Goal is complete. End date set to {goal.end_actual}')
                db.update(goal)
                print('Goal updated.')
        return redirect("/", code=302)

    @app.route('/releases', methods=["GET"])
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

    @app.route('/artists', methods=["GET"])
    def artists():
        countries = db.get_distinct_col(db.Artist, 'country')
        data = {"countries": countries}
        return render_template('artists.html', data=data, active_page='artists')

    @app.route('/labels', methods=["GET"])
    def labels():
        countries = db.get_distinct_col(db.Label, 'country')
        types = db.get_distinct_col(db.Label, 'type')
        data = {"countries": countries, "types": types}
        return render_template('labels.html', data=data, active_page='labels')

    @app.route('/release/<string:release_id>', methods=['GET'])
    def release(release_id):
        # Displays all info related to a particular release
        release_data = db.exists('release', release_id)[0]
        artist_data = db.exists('artist', release_data.artist_id)[0]
        label_data = db.exists('label', release_data.label_id)[0]
        existing_reviews = db.get_release_reviews(release_id)
        data = {"release": release_data,
                "artist": artist_data,
                "label": label_data,
                "reviews": existing_reviews}
        return render_template('release.html', data=data)

    @app.route('/artist/<string:artist_id>', methods=['GET'])
    def artist(artist_id):
        # Displays all info related to a particular artist
        artist_data = db.exists(item_type='artist', item_id=artist_id)[0]
        artist_releases = db.get_artist_releases(artist_id)
        data = {"artist": artist_data, "releases": artist_releases}
        return render_template('artist.html', data=data)

    @app.route('/label/<string:label_id>', methods=['GET'])
    def label(label_id):
        label_data = db.exists(item_type='label', item_id=label_id)[0]
        label_releases = db.get_label_releases(label_id)
        data = {"label": label_data, "releases": label_releases}
        return render_template('label.html', data=data)

    # @app.route('/charts', methods=['GET'])
    # def charts():
    #     # Not implemented
    #     # con = db.create_connection('music.db')
    #     # cur = db.create_cursor(con)
    #     #
    #     # query = "SELECT rating FROM release"
    #     # cur.execute(query)
    #     # data = cur.fetchall()
    #     #
    #     # data = [n[0] for n in data]
    #     # return flask.render_template('charts.html', data=data)
    #     return redirect('/', 302)

    @app.route('/edit/<string:release_id>', methods=['GET'])
    def edit(release_id):
        release_data = db.exists(item_type='release', item_id=release_id)[0]
        label_id = release_data.label_id
        label_data = db.exists(item_type='label', item_id=label_id)[0]
        artist_id = release_data.artist_id
        artist_data = db.exists(item_type='artist', item_id=artist_id)[0]
        return render_template('edit.html',
                               release=release_data,
                               artist=artist_data,
                               label=label_data)

    @app.route('/edit_release', methods=['POST'])
    def edit_release():
        edit_data = request.form.to_dict()
        updated_release = db.construct_item('release', edit_data)
        db.update(updated_release)
        return redirect('/', 302)

    @app.route('/delete', methods=['POST', 'GET'])
    def delete():
        data = request.get_json()
        deletion_id = data['id']
        deletion_type = data['type']
        print(f'Deleting {deletion_type} {deletion_id}')
        db.delete(item_type=deletion_type, item_id=deletion_id)
        return redirect('/', 302)

    @app.route('/add_review', methods=['POST'])
    def add_review():
        review_data = request.form.to_dict()
        new_review = db.construct_item('review', review_data)
        db.insert(new_review)
        return redirect(request.referrer, 302)

    @app.route('/stats', methods=['GET'])
    def stats():
        statistics = get_stats()
        return render_template('stats.html', data=statistics, active_page='stats')

    @app.route('/dynamic_search', methods=['POST'])
    def dynamic_search():
        data = request.get_json()
        origin = data["referrer"]
        del data["referrer"]
        if origin in ['release', 'artist', 'label']:
            search_data = db.dynamic_search(data)
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
            start, end = util.get_page_range(per_page, page)

            paged_data = full_data[start:end]

        elif origin == 'page_button':
            page = data["next_page"]
            per_page = data["per_page"]
            full_data = data["data"]
            start, end = util.get_page_range(per_page, page)
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

    @app.route('/submit_manual', methods=['POST'])
    def submit_manual():
        data = request.form.to_dict()
        db.submit_manual(data)
        return redirect('/', 302)

    @app.route('/goals', methods=['GET'])
    def goals():
        existing_goals = db.get_incomplete_goals()
        data = {
            "today": util.today(),
            "existing_goals": existing_goals
        }
        return render_template('goals.html', active_page='goals', data=data)

    @app.route('/add_goal', methods=['POST'])
    def add_goal():
        data = request.form.to_dict()
        goal = db.construct_item(model_name='goal', data_dict=data)
        db.insert(goal)
        return redirect('/goals', 302)

    @app.route('/migrate', methods=['GET'])
    def migrate():
        util.db_migrate()
        print('Migration successful')
        return redirect('/', 302)
    
