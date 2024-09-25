from .base import app_db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract

def get_model(model_name: str) -> SQLAlchemy.Model:
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
                            "Ensure all valid models are imported and reflect existing models as defined in models.py")
        else:
            return instance


def construct_item(model_name: str,
                   data_dict: dict) -> SQLAlchemy.Model:
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
         prev_id: int):
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

def apply_date_filter(query: SQLAlchemy.Model.query,
                      model: SQLAlchemy.Model,
                      key: str,
                      op: str,
                      value: str):
    """
    Used by dynamic_(artist|label)_search to perform comparisons on begin_date and end_date
    :param query: An instance of a database model query class
    :param model: The database model class to filter on
    :param key: The column to filter on - begin_date or end_date
    :param op: Denotes the comparison to perform; -1 = lt, 0 = eq, 1 = gt
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

    if op == '-1':
        query = query.filter(extract('year', attribute) < val)
    elif op == '0':
        query = query.filter(extract('year', attribute) == val)
    elif op == '1':
        query = query.filter(extract('year', attribute) > val)
    else:
        raise ValueError(f'Invalid op: {op}')
    return query


