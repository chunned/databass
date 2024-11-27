from .base import app_db
from .models import Artist, Release, Label, MusicBrainzEntity, Base, Goal, Tag, Review
from sqlalchemy import extract, Integer
from sqlalchemy.orm import query as sql_query
from sqlalchemy.engine.row import Row
from typing import Type
from datetime import date

def get_model(model_name: str) -> Base | None:
    """
    :param model_name: String corresponding to a database model class
    :return: Instance of that model's class if it exists; None otherwise
    """
    if not isinstance(model_name, str):
        raise ValueError("model_name must be a string")
    else:
        model_name = model_name.lower()
        model_name = model_name.capitalize()
        instance = globals().get(model_name)
        if not instance:
            raise NameError(f"No model with the name '{model_name}' found in globals()."
                            "Ensure all valid models are imported in databass.db.util.py and reflect existing models as defined in models.py")
        else:
            return instance


def construct_item(model_name: str,
                   data_dict: dict) -> Base:
    """
    Construct an instance of a model from a dictionary
    :param model_name: String corresponding to SQLAlchemy model class from models.py
    :param data_dict: Dictionary containing keys corresponding to the database model class
    :return: The newly constructed instance of the model class.
    """
    valid_models = ['release', 'artist', 'label', 'goal', 'review', 'tag']
    if model_name not in valid_models:
        raise ValueError(f"Invalid model name: {model_name} - "
                         f"Model name should be one of: {', '.join(valid_models)}")
    else:
        model = get_model(model_name)
        if model is not None:
            item = model(**data_dict)
            return item
        else:
            raise NameError(f"No model with the name '{model_name}' found in globals()."
                            "Ensure all valid models are imported and reflect existing models as defined in models.py")


def next_item(item_type: str,
         prev_id: int) -> Base:
    """
    Fetches the next entry in the database with an id greater than prev_id
    :return: False if no entry exists; object for the entry otherwise
    """
    if item_type not in ['artist', 'release', 'label']:
        raise ValueError(f'Invalid item_type: {item_type}')
    else:
        model = get_model(item_type)
        query = model.query
        item = query.filter(model.id > prev_id).first()
        return item if item else False

def apply_comparison_filter(query,
                      model: Type[MusicBrainzEntity],
                      key: str,
                      operator: str,
                      value: str) -> sql_query:
    """
    Used by dynamic_search to perform comparisons on begin_date, end_date, year, or rating
    :param query: An SQLAlchemy query class
    :param model: The database model class to filter on
    :param key: The column to filter on - begin_date or end_date
    :param operator: Denotes the comparison to perform
    :param value: The value to compare against
    :return: Newly constructed query
    """
    attribute = getattr(model, key)
    if not attribute:
        raise NameError(f"No attribute '{key}' found in model {model}")
    try:
        val = int(value)
    except TypeError:
        raise TypeError(f"Value must be an integer, got {type(value)}: {value}")

    if operator not in ['<', '=', '>']:
        raise ValueError(f"Unrecognized operator value for year_comparison: {operator}")

    if key == 'begin_date' or key == 'end_date':

        query = query.filter(extract('year', attribute).cast(Integer).op(operator)(val))
    elif key == 'rating':
        query = query.filter(Release.rating.op(operator)(value))
    elif key == 'release_year':
        query = query.filter(Release.release_year.op(operator)(value))
    return query


# Utility function to calculate the mean average rating and total release count for releases associated with a specific Label/Artist
def mean_avg_and_count(entities: list[Row]) -> (int, int):
    """
    :param entities: List of SQLAlchemy Rows; returned from average_ratings_and_total_counts()
    :return: A tuple representing the mean average release rating and mean release count
    """
    avg = count = 0
    total = len(entities)
    for item in entities:
        try:
            avg += int(item.average_rating)
            count += int(item.release_count)
        except AttributeError:
            # TODO: consider logging info about the erroring release
            # Have not encountered this in practice, but if it is encountered it means there is a 'corrupted' DB entry
            total -= 1

    mean_avg = avg / total
    mean_count = count / total
    return mean_avg, mean_count


# Utility function used to calculate Bayesian average
def bayesian_avg(
        item_weight: float,
        item_avg: float,
        mean_avg: float
) -> float:
    """
    Calculates the Bayesian average rating for a given item weight and average
    :param item_weight: Float representing the item's weight for the formula; calculated as: count / (count + mean count)
    :param item_avg: Item's average rating
    :param mean_avg: Mean average release rating for all database entries
    :return: Float representing the Bayesian average rating for releases associated with this item
    """
    if not item_weight or not item_avg or not mean_avg:
        raise ValueError(f"Input missing one of the required values")
    return item_weight * item_avg + (1 - item_weight) * mean_avg


def get_all_stats():
    stats = {
        "total_listens": Release.total_count(),
        "total_artists": Artist.total_count(),
        "total_labels": Label.total_count(),
        "average_rating": Release.ratings_average(),
        "average_runtime": Release.average_runtime(),
        "total_runtime": Release.total_runtime(),
        "releases_this_year": Release.added_this_year(),
        "artists_this_year": Artist.added_this_year(),
        "labels_this_year": Label.added_this_year(),
        "releases_per_day": Release.added_per_day_this_year(),
        "artists_per_day": Artist.added_per_day_this_year(),
        "labels_per_day": Label.added_per_day_this_year(),
        "top_rated_labels": Label.average_ratings_bayesian()[0:10],
        "top_rated_artists": Artist.average_ratings_bayesian()[0:10],
        "top_frequent_labels": Label.frequency_highest()[0:10],
        "top_frequent_artists": Artist.frequency_highest()[0:10],
        "top_average_artists": Artist.average_ratings_and_total_counts()[0:10],
        "top_average_labels": Label.average_ratings_and_total_counts()[0:10],
    }
    return stats


def handle_submit_data(submit_data: dict) -> None:
    from ..api import MusicBrainz
    from .models import Goal, Tag, Release, Artist, Label
    runtime = MusicBrainz.get_release_length(submit_data["mbid"])

    submit_data["runtime"] = runtime

    if submit_data["label_mbid"]:
        label_id = Label.create_if_not_exist(
            mbid=submit_data["label_mbid"],
            name=submit_data["label_name"],
        )
    else:
        label_id = 0

    submit_data["label_id"] = label_id

    if submit_data["artist_mbid"]:
        artist_id = Artist.create_if_not_exist(
            mbid=submit_data["artist_mbid"],
            name=submit_data["artist_name"],
        )
    else:
        artist_id = 0

    submit_data["artist_id"] = artist_id
    release_id = Release.create_new(submit_data)

    if submit_data["tags"] is not None:
        Tag.create_tags(submit_data["tags"], release_id)
    Goal.check_goals()

