from .base import app_db
from .models import Artist, Release, Label, MusicBrainzEntity, Base, Goal, Tag, Review
from sqlalchemy import extract
from sqlalchemy.orm import query as sql_query
from sqlalchemy.engine.row import Row

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
                      model: MusicBrainzEntity,
                      key: str,
                      operator: str,
                      value: str) -> sql_query:
    """
    Used by dynamic_search to perform comparisons on begin_date, end_date, year, or rating
    :param query: An SQLAlchemy query class
    :param model: The database model class to filter on
    :param key: The column to filter on - begin_date or end_date
    :param operator: Denotes the comparison to perform; -1 = lt, 0 = eq, 1 = gt
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

    if operator not in ['-1', '0', '1']:
        raise ValueError(f"Unrecognized operator value for year_comparison: {operator}")

    if key == 'begin_date' or key == 'end_date':
        if operator == '-1':
            query = query.filter(extract('year', attribute) < val)
        elif operator == '0':
            query = query.filter(extract('year', attribute) == val)
        elif operator == '1':
            query = query.filter(extract('year', attribute) > val)
    elif key == 'rating':
        if operator == '-1':
            query = query.filter(Release.rating < value)
        elif operator == '0':
            query = query.filter(Release.rating == value)
        elif operator == '1':
            query = query.filter(Release.rating > value)
    elif key == 'year':
        if operator == '-1':
            query = query.filter(Release.release_year < value)
        elif operator == '0':
            query = query.filter(Release.release_year == value)
        elif operator == '1':
            query = query.filter(Release.release_year > value)

    return query


def get_all_id_and_img() -> dict:
    """
    Retrieve all IDs and images from the database
    :return: Dictionary containing all IDs and images
    """
    releases = app_db.session.query(
        Release.id, Release.image
    ).all()
    artists = app_db.session.query(
        Artist.id, Artist.image
    ).all()
    labels = app_db.session.query(
        Label.id, Label.image
    ).all()
    data = {
        "releases": releases,
        "artists": artists,
        "labels": labels
    }
    return data

# Utility function to calculate the mean average rating and total release count for releases associated with a specific Label/Artist
def mean_avg_and_count(entities: list[Row]) -> (int, int):
    """
    :param entities: List of SQLAlchemy Rows; returned from average_ratings_and_total_counts()
    :return: A tuple representing the mean average release rating and mean release count
    """
    avg = count = 0
    total = len(entities)
    for item in entities:
        avg += int(item.average_rating)
        count += int(item.release_count)
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
    return item_weight * item_avg + (1 - item_weight) * mean_avg