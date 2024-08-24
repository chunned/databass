import sqlalchemy
from sqlalchemy import func, extract
import datetime
import pytz
from dotenv import load_dotenv
import os
from models import app_db, Release, Label, Artist, Goal

load_dotenv()
TIMEZONE = os.getenv('TIMEZONE')


def insert_item(item):
    # Insert an instance of one of the table classes
    try:
        app_db.session.add(item)
        app_db.session.commit()
        return item.id
    except sqlalchemy.exc.IntegrityError as err:
        app_db.session.rollback()
        print(f'SQLite Integrity Error: \n{err}\n')
    except Exception as err:
        app_db.session.rollback()
        print(f'Unexpected error: {err}')


def insert_release(release):
    # Construct an instance of the Release class, then insert it
    new_release = Release(
        mbid=release.get("mbid"),
        artist_id=release.get("artist_id", 0),
        label_id=release.get("label_id", 0),
        name=release.get("name"),
        release_year=release.get("release_year", 0),
        runtime=release.get("runtime", 0),
        rating=release.get("rating"),
        listen_date=release.get("listen_date"),
        track_count=release.get("track_count"),
        country=release.get("country", 0),
        image=release.get("image", ''),
        genre=release.get("genre"),
        tags=release.get("tags", '')
    )
    release_id = insert_item(new_release)
    return release_id


def insert_artist(artist):
    # Construct an instance of the Artist class, then insert it
    new_artist = Artist(
        mbid=artist.get("mbid", "0"),
        name=artist.get("name"),
        country=artist.get("country", ""),
        type=artist.get("type", ""),
        begin_date=artist.get("begin_date", ""),
        end_date=artist.get("end_date", ""),
        image=artist.get("image")
    )
    artist_id = insert_item(new_artist)
    return artist_id


def insert_label(label):
    # Construct an instance of the Label class, then insert it
    new_label = Label(
        mbid=label.get("mbid", "0"),
        name=label.get("name"),
        country=label.get("country", ""),
        type=label.get("type", ""),
        begin_date=label.get("begin_date", ""),
        end_date=label.get("end_date", ""),
        image=label.get("image")
    )
    label_id = insert_item(new_label)
    return label_id


def insert_goal(goal):
    new_goal = Goal(
        start_date=goal.get("start_date"),
        end_goal=goal.get("end_goal"),
        end_actual="0",
        type=goal.get("type"),
        amount=goal.get("amount")
    )
    goal_id = insert_item(new_goal)
    return goal_id


def get_stats():
    current_year = str(datetime.datetime.now().year)
    days_this_year = datetime.date.today().timetuple().tm_yday
    # Check if any releases are in the database. If not, skip stats
    db_length = app_db.session.query(func.count(Release.id)).scalar()
    if db_length == 0:
        return ''

    stats = {"total_listens": app_db.session.query(Release.id).count(),
             "total_artists": app_db.session.query(Artist).count(),
             "total_labels": app_db.session.query(Label).count(),
             "average_rating": app_db.session.query(
                 func.round(
                     func.avg(Release.rating), 2)
             ).scalar(),
             "average_runtime": round(
                 (
                         (
                             app_db.session.query(
                                 func.avg(
                                     Release.runtime
                                 )
                             ).scalar()
                         ) / 60000
                 ), 2
             ),
             "total_runtime": round(
                 (
                         (
                             app_db.session.query(
                                 func.sum(
                                     Release.runtime
                                 )
                             ).scalar()
                         ) / 3600000
                 ), 2
             ),
             "listens_this_year": app_db.session.query(func.count(Release.id)).filter(
                 extract('year', Release.listen_date) == current_year
             ).scalar()
             }
    listens_per_day = stats["listens_this_year"] / days_this_year
    stats["listens_per_day"] = round(listens_per_day, 2)

    # Top rated labels
    query = (
        app_db.session.query(
            Label.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.label_id).label('release_count')
        )
        .join(Release, Release.label_id == Label.id)
        .filter(
            Label.name.notin_(['none', '[no label]']))  # Don't count the entries corresponding to no label for release
        .group_by(Label.name)
        .having(func.count(Release.label_id) != 1)  # Don't count labels with only 1 release
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'average_rating': row.average_rating,
                'release_count': row.release_count}
               for row in query]
    stats["favourite_labels"] = results

    # Highest rated artists
    query = (
        app_db.session.query(
            Artist.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.artist_id).label('release_count')
        )
        .join(Release, Release.artist_id == Artist.id)
        .group_by(Artist.name)
        .having(func.count(Release.artist_id) != 1)
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'average_rating': row.average_rating,
                'release_count': row.release_count}
               for row in query]
    stats["favourite_artists"] = results

    # Most frequent labels
    query = (
        app_db.session.query(
            Label.name,
            func.count(Release.label_id).label('count')
        )
        .join(Release, Release.label_id == Label.id)
        .group_by(Label.name)
        .order_by(func.count(Release.label_id).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'count': row.count}
               for row in query]
    stats["frequent_labels"] = results

    # Most frequent artists
    query = (
        app_db.session.query(
            Artist.name,
            func.count(Release.artist_id).label('count')
        )
        .join(Release, Release.artist_id == Artist.id)
        .where(Artist.name != "Various Artists")
        .group_by(Artist.name)
        .order_by(func.count(Release.artist_id).desc())
        .limit(5)
        .all()
    )
    results = [{'name': row.name,
                'count': row.count}
               for row in query]
    stats["frequent_artists"] = results

    return stats


def get_homepage_data():
    home_data = (
        app_db.session.query(
            Artist.id,
            Artist.name,
            Release.id,
            Release.name,
            Release.rating,
            Release.listen_date,
            Release.genre,
            Release.image,
            Release.tags
        )
        .join(Artist, Artist.id == Release.artist_id)
        .order_by(Release.id.desc())
    )
    return home_data


def get_items(item_type):
    # Gets all items of a specified type
    if item_type == 'releases':
        items = app_db.session.query(Release)
    elif item_type == 'artists':
        items = app_db.session.query(Artist)
    elif item_type == 'labels':
        items = app_db.session.query(Label)
    else:
        raise ValueError('ERROR: Invalid item_type: ', item_type)
    return items


def get_item(item_type, item_id):
    # Gets a single item specified by its ID
    if item_type == 'release':
        release = app_db.session.query(Release).where(Release.id == item_id).first()
        artist = app_db.session.query(Artist).where(Artist.id == release.artist_id).first()
        label = app_db.session.query(Label).where(Label.id == release.label_id).first()
        item_data = {
            "release": release,
            "artist": artist,
            "label": label
        }
    elif item_type == 'artist':
        artist = app_db.session.query(Artist).where(Artist.id == item_id).all()
        releases = (app_db.session.query(Release, Label.name)
                    .join(Label, Release.label_id == Label.id)
                    .join(Artist, Artist.id == Release.artist_id)
                    .where(Artist.id == item_id)
                    .all()
                    )
        item_data = {
            "artist": artist[0],
            "releases": releases
        }
    elif item_type == 'label':
        label = app_db.session.query(Label).where(Label.id == item_id).all()
        releases = (app_db.session.query(Release, Artist)
                    .join(Artist, Artist.id == Release.artist_id)
                    .where(Release.label_id == item_id)
                    ).all()
        item_data = {
            "label": label[0],
            "releases": releases
        }
    else:
        raise ValueError('ERROR: Invalid item_type: ', item_type)
    return item_data


def exists(mbid, item_type):
    # mbid = the MusicBrainz ID for the entity
    # item_type = release, artist, or label
    # Returns a 2 element array:
    # - 1: True if an item exists in the database, False otherwise
    # - 2: Item's ID (primary key) in the database if it exists, None otherwise
    if item_type == 'label':
        q = app_db.session.query(Label.id).where(Label.mbid == mbid).scalar()
    elif item_type == 'artist':
        q = app_db.session.query(Artist.id).where(Artist.mbid == mbid).scalar()
    elif item_type == 'release':
        q = app_db.session.query(Release.id).where(Release.mbid == mbid).scalar()
    else:
        raise ValueError('Invalid item_type passed')
    if q:
        return [True, q]
    else:
        return [False, q]


def delete_item(item_type, item_id):
    if item_type == 'release':
        release = app_db.session.execute(
            app_db.select(Release).where(Release.id == item_id)
        ).scalar_one_or_none()
        app_db.session.delete(release)
        app_db.session.commit()
    elif item_type == 'artist':
        artist = app_db.session.execute(
            app_db.select(Artist).where(Artist.id == item_id)
        ).scalar_one_or_none()
        app_db.session.delete(artist)
        app_db.session.commit()
    elif item_type == 'label':
        label = app_db.session.execute(
            app_db.select(Label).where(Label.id == item_id)
        ).scalar_one_or_none()
        app_db.session.delete(label)
        app_db.session.commit()
    else:
        raise ValueError("ERROR: Invalid item_type")
    return 0


def update_release(edit_data):
    # edit_data is a dictionary POSTed from /edit/<release>
    release_id = edit_data['release_id']
    release_entry = get_item(item_type='release', item_id=release_id)['release']
    release_entry.listen_date = edit_data['listen_date']
    release_entry.rating = edit_data['rating_edit']
    release_entry.release_year = edit_data['release_year']
    release_entry.genre = edit_data['genre']
    release_entry.tags = edit_data['tags']
    release_entry.country = edit_data['country']
    release_entry.image = edit_data['image']
    app_db.session.commit()
    return 0


def add_review(data):
    release_id = data['release_id']
    review = data['review']

    release = app_db.session.query(Release).where(Release.id == release_id).one_or_none()
    release.review = review
    app_db.session.commit()
    return 0


def distinct_entries(table, column):
    # Column should correspond to a column in the database table (one of the model class attributes)
    if not hasattr(table, '__table__'):
        raise ValueError('Invalid table')
    if not hasattr(table, column):
        raise ValueError('Invalid column for this table')

    col = getattr(table, column)
    distinct = app_db.session.query(sqlalchemy.distinct(col)).order_by(col).all()
    # distinct comes out as a list of tuples so below unpacks into just a list
    return [genre[0] for genre in distinct]


def submit_manual(data):
    print(data)
    label_name = data["label"]
    existing_label = check_item_by_name('label', label_name)
    if existing_label is not None:
        label_id = existing_label[0]
    else:
        label = Label()
        label.name = label_name
        label_id = insert_item(label)

    artist_name = data["artist"]
    existing_artist = check_item_by_name('artist', artist_name)
    if existing_artist is not None:
        artist_id = existing_artist[0]
    else:
        artist = Artist()
        artist.name = artist_name
        artist_id = insert_item(artist)

    local_timezone = pytz.timezone(TIMEZONE)

    release = Release()
    release.name = data["name"]
    release.artist_id = artist_id
    release.label_id = label_id
    release.release_year = data["release_year"]
    release.rating = data["rating"]
    release.genre = data["genre"]
    release.tags = data["tags"]
    release.image = data["image"]
    release.listen_date = datetime.datetime.now(local_timezone).strftime("%Y-%m-%d")
    insert_item(release)


def check_item_by_name(item_type, name):
    if item_type == 'artist':
        result = app_db.session.query(Artist.id).where(func.lower(Artist.name) == func.lower(name)).one_or_none()
    elif item_type == 'label':
        result = app_db.session.query(Label.id).where(func.lower(Label.name) == func.lower(name)).one_or_none()
    elif item_type == 'release':
        result = app_db.session.query(Label.id).where(func.lower(Label.name) == func.lower(name)).one_or_none()
    else:
        raise ValueError('Invalid item_type')
    return result


def dynamic_search(data):
    # data is a dictionary POSTed from /releases, /artists, or /labels
    # we don't know which form fields will be populated beforehand
    print(f'INFO: SEARCH DATA: {data}')
    populated_fields = {}
    for key, value in data.items():
        if 'comparison' in key or key == 'qtype':
            print('INFO: Utility field, not meant to be in the query, moving on')
        else:
            if value != '':
                # print(f'CURRENT DATA ITEM: {key}, {value}')
                if data['qtype'] == 'release':
                    return_data = ["release"]
                    if key == 'label':
                        # print('LABEL IDENTIFIED - QUERYING')
                        try:
                            label_id = (
                                Label.query.filter(
                                    func.lower(Label.name) == func.lower(value)
                                )
                                .first()
                                .id
                            )
                            populated_fields['label_id'] = label_id
                            # print(f'LABEL FOUND WITH ID {label_id}')
                        except AttributeError:
                            print('ERROR: Label does not exist')
                    elif key == 'artist':
                        # print('ARTIST IDENTIFIED - QUERYING')
                        try:
                            artist_id = (
                                Artist.query.filter(
                                    Artist.name.ilike(
                                        f'%{value}%'
                                    )
                                )
                                .first()
                                .id
                            )
                            populated_fields['artist_id'] = artist_id
                            # print(f'ARTIST FOUND WITH ID {artist_id}')
                        except AttributeError:
                            print('Artist does not exist')
                    elif key == 'country' and value == 'NO VALUE':
                        print('INFO: Country empty, moving on')
                    elif key in ['rating', 'year']:
                        populated_fields[key] = int(value)
                    else:
                        print('OTHER KEY FOUND; ADDING TO POPULATED FIELDS')
                        print(key, value)
                        populated_fields[key] = value
                    print(f'INFO: Populated Fields: {populated_fields}')
                    query = Release.query
                    for k, v in populated_fields.items():
                        print(f'current key: {k}')
                        print(f'INFO: Adding to query: {key}, {value}')
                        if k == 'rating':
                            op = data['rating_comparison']
                            if op == '-1':
                                # print('OPERATOR: Less than')
                                query = query.filter(Release.rating < v)
                            elif op == '0':
                                # print('OPERATOR: Equal')
                                query = query.filter(Release.rating == v)
                            elif op == '1':
                                query = query.filter(Release.rating > v)
                                # print('OPERATOR: Greater than')
                        elif k == 'year':
                            op = data['year_comparison']
                            if op == '-1':
                                # print('OPERATOR: Less than')
                                query = query.filter(Release.release_year < v)
                            elif op == '0':
                                # print('OPERATOR: Equal')
                                query = query.filter(Release.release_year == v)
                            elif op == '1':
                                # print('OPERATOR: Greater than')
                                query = query.filter(Release.release_year > v)
                        elif k == 'name':
                            query = query.filter(
                                Release.name.ilike(f'%{v}%')
                            )
                        else:
                            query = query.filter(getattr(Release, k) == v)
                        print(f'IFNO: Results after this query: {query.all()}')

                elif data['qtype'] == 'artist':
                    return_data = ["artist"]
                    if key == 'country' and value == 'NO VALUE':
                        print('INFO: Country empty, moving on')
                    elif key == 'type' and value == 'NO VALUE':
                        print('INFO: Type empty, moving on')
                    else:
                        populated_fields[key] = value
                    print(f'POPULATED FIELDS: {populated_fields}')
                    query = Artist.query
                    for k, v in populated_fields.items():
                        if k == 'name':
                            query = query.filter(
                                Artist.name.ilike(f'%{v}%')
                            )
                        elif k == 'country':
                            print(f'Filtering for country like {v}')
                            query = query.filter(
                                Artist.country == v
                            )
                        elif k == 'begin_date':
                            op = data["begin_comparison"]
                            if op == '-1':
                                query = query.filter(
                                    extract('year', Artist.begin_date) < int(v)
                                )
                            elif op == '0':
                                query = query.filter(
                                    extract('year', Artist.begin_date) == int(v)
                                )
                            elif op == '1':
                                query = query.filter(
                                    extract('year', Artist.begin_date) > int(v)
                                )
                        elif k == 'end_date':
                            op = data["end_comparison"]
                            if op == '-1':
                                query = query.filter(
                                    extract('year', Artist.end_date) < int(v)
                                )
                            elif op == '0':
                                query = query.filter(
                                    extract('year', Artist.end_date) == int(v)
                                )
                            elif op == '1':
                                query = query.filter(
                                    extract('year', Artist.end_date) > int(v)
                                )

                        else:
                            query = query.filter(getattr(Artist, k) == v)

                elif data['qtype'] == 'label':
                    return_data = ["label"]
                    if key == 'country' and value == 'NO VALUE':
                        print('INFO: Country empty, moving on')
                    elif key == 'type' and value == 'NO VALUE':
                        print('INFO: Type empty, moving on')
                    else:
                        populated_fields[key] = value
                    query = Label.query
                    for k, v in populated_fields.items():
                        if k == 'name':
                            query = query.filter(
                                Release.name.ilike(f'%{v}%')
                            )
                        elif k == 'begin_date':
                            op = data["begin_comparison"]
                            if op == '-1':
                                query = query.filter(
                                    extract('year', Label.begin_date) < int(v)
                                )
                            elif op == '0':
                                query = query.filter(
                                    extract('year', Label.begin_date) == int(v)
                                )
                            elif op == '1':
                                query = query.filter(
                                    extract('year', Label.begin_date) > int(v)
                                )
                        elif k == 'end_date':
                            op = data["end_comparison"]
                            if op == '-1':
                                query = query.filter(
                                    extract('year', Label.end_date) < int(v)
                                )
                            elif op == '0':
                                query = query.filter(
                                    extract('year', Label.end_date) == int(v)
                                )
                            elif op == '1':
                                query = query.filter(
                                    extract('year', Label.end_date) > int(v)
                                )
                        else:
                            query = query.filter(getattr(Label, k) == v)
                else:
                    raise ValueError('Invalid qtype; must be one of [release, artist, label]')

    return_data.append(query.all())
    print(return_data)

    # print("FINAL QUERY DATA:")
    # print(data)
    return return_data


def get_all_id_and_img():
    releases = app_db.session.query(
        Release.id, Release.image
    ).all()
    artists = app_db.session.query(
        Artist.id, Artist.image
    )
    labels = app_db.session.query(
        Label.id, Label.image
    )
    data = {
        "releases": releases,
        "artists": artists,
        "labels": labels
    }
    return data


# ---- INCOMPLETE -----
def update_artist():
    return 0


def update_label():
    return 0


# below should maybe be moved elsewhere
def get_missing_covers():
    return 0


def get_missing_artist_data():
    return 0


def get_missing_label_data():
    return 0
