from .base import app_db
from .util import apply_date_filter, get_model
from .operations import insert
from ..models import Release, Label, Artist, Review, Tag, Goal
from sqlalchemy import func, distinct
from dotenv import load_dotenv
from os import getenv
from datetime import datetime
from pytz import timezone
from flask_sqlalchemy import SQLAlchemy
from typing import Union

load_dotenv()
TIMEZONE = getenv('TIMEZONE')


# def exists(item_type: str,
#            item_id: int = -1,
#            mbid: str = '',
#            name: str = '') -> Union[SQLAlchemy.Model, bool]:
#     """
#     Check if an entry exists in the database matching a given MusicBrainzID or name
#     :param item_type: Item's type, corresponding to a database model class from models.py
#     :param item_id: Optional - item's ID
#     :param mbid: Optional - item's MusicBrainzID
#     :param name: Optional - item's name
#     :return: Item object if item exists, False otherwise
#     """
#     if item_id == -1 and mbid == '' and name == '':
#         raise ValueError("No identifying information provided. At least one of item_id, mbid or name is required.")
#
#     model = get_model(item_type)
#     if not model:
#         raise Exception(f'No database model found with the name {item_type}.')
#     query = model.query
#     if item_id > -1:
#         query = query.filter(model.id == item_id)
#     if mbid:
#         query = query.filter(model.mbid == mbid)
#     if name:
#         query = query.filter(model.name.ilike(f'%{name}%'))
#
#     result = query.one_or_none()
#     if result:
#         return result
#     else:
#         return False


# def get_artist_releases(artist_id: int) -> Union[list, None]:
#     """
#     Returns all releases related to the artist_id passed in
#     :param artist_id: The ID of an Artist
#     :return: All releases associated with this ID
#     """
#     if not isinstance(artist_id, int):
#         raise TypeError(f'artist_id should be an integer, got a {type(artist_id)}: {artist_id}')
#     releases = (
#         app_db.session.query(Release, Label.name)
#         .join(Label, Release.label_id == Label.id)
#         .join(Artist, Artist.id == Release.artist_id)
#         .where(Artist.id == artist_id)
#     ).all()
#     if releases:
#         return releases
#     else:
#         return None

# def get_label_releases(label_id: int) -> Union[list, None]:
#     """
#     :param label_id: The ID of a Label
#     :return: All releases associated with this ID
#     """
#     if not isinstance(label_id, int):
#         raise TypeError(f'label_id should be an integer, got a {type(label_id)}: {label_id}')
#     releases = (
#         app_db.session.query(Release, Artist)
#         .join(Artist, Artist.id == Release.artist_id)
#         .where(Release.label_id == label_id)
#     ).all()
#     if releases:
#         return releases
#     else:
#         return None


# def get_release_reviews(release_id: int) -> Union[list, None]:
#     """
#     :param release_id: ID of the release to filter by
#     :return: All reviews for the release ID
#     """
#     if not isinstance(release_id, int):
#         raise TypeError(f'release_id should be an integer, got a {type(release_id)}: {release_id}')
#     reviews = (
#         app_db.session.query(
#             func.to_char(Review.timestamp, 'YYYY-MM-DD HH24:MI').label('timestamp'),
#             Review.text
#         ).where(Review.release_id == release_id)
#     ).all()
#     if reviews:
#         return reviews
#     else:
#         return None


# def get_all(item_type: str) -> Union[list, None]:
#     """
#     Get all entries of a given SQLAlchemy model class
#     :param item_type: String corresponding to database model class
#     :return: All entries for that class
#     """
#     model = get_model(item_type)
#     if model:
#         results = model.query.all()
#         if results:
#             return results
#         else:
#             return None
#     else:
#         raise NameError(f'No database model found with the name {item_type}.')

# def get_distinct_col(table: app_db.Model,
#                      col: str) -> list:
#     """
#     Get distinct values of a non-unique column from the database
#     :param table: Model class to query against
#     :param col: Column for which unique values are to be retrieved
#     :return: Distinct values for the column
#     """
#     try:
#         attribute = hasattr(table, col)
#         if attribute:
#             query = app_db.session.query(
#                 distinct(attribute)
#             )
#             result = query.all()
#             if result:
#                 distinct_values = [val[0] for val in query.all()]
#                 return distinct_values
#             else:
#                 # TODO: figure out proper exception type for nothing found by query
#                 pass
#         else:
#             raise AttributeError
#     except AttributeError:
#         raise AttributeError('Model class does not have a matching column')



# def get_all_id_and_img() -> dict:
#     """
#     Retrieve all IDs and images from the database
#     :return: Dictionary containing all IDs and images
#     """
#     releases = app_db.session.query(
#         Release.id, Release.image
#     ).all()
#     artists = app_db.session.query(
#         Artist.id, Artist.image
#     ).all()
#     labels = app_db.session.query(
#         Label.id, Label.image
#     ).all()
#     data = {
#         "releases": releases,
#         "artists": artists,
#         "labels": labels
#     }
#     return data


# def dynamic_search(data: dict):
#     """
#     Query data from the database. Used for /releases, /labels, /artists
#     :param data: Dictionary containing data to query by
#     :return: Results of a query returned from a dynamic_Model_search() function
#     """
#     if data['qtype'] == 'release':
#         return ["release", dynamic_release_search(data)]
#     elif data['qtype'] == 'artist':
#         return ["artist", dynamic_artist_search(data)]
#     elif data['qtype'] == 'label':
#         return ["label", dynamic_label_search(data)]


# def dynamic_release_search(data: dict):
#     """
#     Query existing data entries from the database. Used for /releases
#     :param data: A dictionary containing terms to filter by
#     :return: Results of the constructed query
#     """
#     query = Release.query
#     for key, value in data.items():
#         if 'comparison' in key or key == 'qtype':
#             # Utility field, not meant to be queried by
#             pass
#         elif value != '' and value != 'NO VALUE' and value != ['NO VALUE']:
#             # If value is non-empty, add it to query
#             if key == 'label':
#                 search_label = exists(item_type='Label', name=value)
#                 label_id = [label.id for label in search_label]
#                 query = query.filter(Release.label_id.in_(label_id))
#             elif key == 'artist':
#                 search_artist = exists(item_type='artist', name=value)
#                 artist_id = [artist.id for artist in search_artist]
#                 query = query.filter(Release.artist_id.in_(artist_id))
#             elif key == 'rating':
#                 # op denotes the type of comparison to make
#                 # -1 = less than; 0 = equal; 1 = greater than
#                 op = data['rating_comparison']
#                 if op == '-1':
#                     query = query.filter(Release.rating < value)
#                 elif op == '0':
#                     query = query.filter(Release.rating == value)
#                 elif op == '1':
#                     query = query.filter(Release.rating > value)
#             elif key == 'year':
#                 # op denotes the type of comparison to make
#                 # -1 = less than; 0 = equal; 1 = greater than
#                 op = data['year_comparison']
#                 if op == '-1':
#                     query = query.filter(Release.release_year < value)
#                 elif op == '0':
#                     query = query.filter(Release.release_year == value)
#                 elif op == '1':
#                     query = query.filter(Release.release_year > value)
#             elif key == 'name':
#                 query = query.filter(
#                     Release.name.ilike(f'%{value}%')
#                 )
#             elif key == 'tags':
#                 print(f'Tags: {value}')
#                 query = query.join(Tag, Tag.release_id == Release.id)
#                 print(query)
#                 for tag in value:
#                     query = query.filter(Tag.name == tag)
#                     print(query)
#             else:
#                 query = query.filter(
#                     getattr(Release, key) == value
#                 )
#     results = query.order_by(Release.id).all()
#     return results


# def dynamic_artist_search(data: dict):
#     """
#     Query existing data entries from the database. Used for /artists
#     :param data: A dictionary containing terms to filter by
#     :return: Results of the constructed query
#     """
#     return dynamic_artist_or_label_query(
#         item_type=Artist,
#         filters=data
#     )
#
#
# def dynamic_label_search(data: dict):
#     """
#     Query existing data entries from the database. Used for /labels
#     :param data: A dictionary containing terms to filter by
#     :return: Results of the constructed query
#     """
#     return dynamic_artist_or_label_query(
#         item_type=Label,
#         filters=dict(data.items())
#     )


# def dynamic_artist_or_label_query(item_type: app_db.Model, filters: dict):
#     """
#     Handles the querying and filtering for dynamic label/artist search
#     :param item_type: Artist or Label
#     :param filters: Dictionary of values to filter by
#     :return: Query object with filters applied
#     """
#     query = item_type.query
#     for key, value in filters.items():
#         if 'comparison' in key or key == 'qtype':
#             # Utility field, not meant to be queried by
#             pass
#         elif value != '' and value != 'NO VALUE':
#             if key == 'name':
#                 query = query.filter(
#                     item_type.name.ilike(f'%{value}%')
#                 )
#             elif key == 'begin_date':
#                 op = filters["begin_comparison"]
#                 query = apply_date_filter(query, item_type, key, op, value)
#             elif key == 'end_date':
#                 op = filters["end_comparison"]
#                 query = apply_date_filter(query, item_type, key, op, value)
#             else:
#                 query = query.filter(
#                     getattr(item_type, key) == value
#                 )
#     query = query.where(
#         item_type.name != "[NONE]"
#     ).where(
#         item_type.name != "[no label]"
#     ).all()
#     return query



# def submit_manual(data):
#     print(data)
#     label_name = data["label"]
#     existing_label = exists(item_type='label', name=label_name)
#     if existing_label is not None:
#         label_id = existing_label.id
#     else:
#         label = Label()
#         label.name = label_name
#         label_id = insert(label)
#
#     artist_name = data["artist"]
#     existing_artist = exists(item_type='artist', name=artist_name)
#     if existing_artist is not None:
#         artist_id = existing_artist.id
#     else:
#         artist = Artist()
#         artist.name = artist_name
#         artist_id = insert(artist)
#
#     local_timezone = timezone(TIMEZONE)
#
#     release = Release()
#     release.name = data["name"]
#     release.artist_id = artist_id
#     release.label_id = label_id
#     release.release_year = data["release_year"]
#     release.rating = data["rating"]
#     release.genre = data["genre"]
#     release.tags = data["tags"]
#     release.image = data["image"]
#     release.listen_date = datetime.now(local_timezone).strftime("%Y-%m-%d")
#     insert(release)


# def get_incomplete_goals() -> Union[list, None]:
#     """
#     Query database for goals without an end_actual date, meaning they have not been completed
#     Returns a list of the goals if found; none otherwise
#     """
#     query = Goal.query.where(Goal.end_actual.is_(None))
#     results = query.all()
#     if results:
#         return results
#     else:
#         return None
