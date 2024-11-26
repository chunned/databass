from __future__ import annotations
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, func, UniqueConstraint, extract, distinct
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, date
from sqlalchemy.engine.row import Row
from typing import Any, Optional, List

from .base import app_db
from ..api import MusicBrainz


class Base(DeclarativeBase):
    """Base class which all other database model classes are built from"""
    id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    def get_all(cls) -> list[Any]:
        # Return all database entries for this class
        results = app_db.session.query(cls).all()
        return results

    @classmethod
    def total_count(cls) -> int:
        # Return the count of all database entries for this class
        try:
            results = app_db.session.query(cls).count()
            return results if isinstance(results, int) else None
        except Exception as e:
            raise RuntimeError(f"Failed to count {cls.__name__} entries") from e

    @classmethod
    def exists_by_id(
            cls,
            item_id: int
    ) -> Optional[Base]:
        """
        Check if an item exists in the database by its ID
        :param item_id: Item's ID (primary key)
        :return: The item, if it exists, or False if the item does not exist
        """
        try:
            result = app_db.session.query(cls).filter(cls.id == item_id).one_or_none()
            return result if result else None
        except Exception as e:
            return None

    @classmethod
    def get_distinct_column_values(
            cls,
            column: str
    ) -> list:
        """
        Get all distinct values of a given column
        :param column: String representing the column's name
        :return: List of the unique values of the given column
        """
        try:
            attribute = getattr(cls, column)
            return [value for (value,) in app_db.session.query(distinct(attribute))]
        except AttributeError as e:
            raise e

app_db.Model = Base

class MusicBrainzEntity(app_db.Model):
    # Release and ArtistOrLabel are built from this prototype
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    mbid: Mapped[str | None] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String())
    image: Mapped[str | None] = mapped_column(String())

    @classmethod
    def exists_by_mbid(
            cls,
            mbid: str
    ) -> Optional[MusicBrainzEntity]:
        """
        Check if a MusicBrainzEntity exists in the database by its MBID (MusicBrainz ID).

        Args:
            mbid (str): The MBID of the MusicBrainzEntity to check for.

        Returns:
            Optional[MusicBrainzEntity]: The MusicBrainzEntity if it exists, otherwise None.
        """
        if not mbid or not isinstance(mbid, str):
            return None
        result = app_db.session.query(cls).filter(cls.mbid == mbid).one_or_none()
        if result:
            return result
        else:
            return None

    @classmethod
    def exists_by_name(
            cls,
            name: str
    ) -> Optional[MusicBrainzEntity]:
        """
        Check if a MusicBrainzEntity exists in the database by its name.

        Args:
            name (str): The name of the MusicBrainzEntity to check for.

        Returns:
            Optional[MusicBrainzEntity]: The MusicBrainzEntity if it exists, otherwise None.
        """
        if not name or not isinstance(name, str):
            return None
        result = app_db.session.query(cls).filter(
            cls.name.ilike(f'%{name}%')
        ).one_or_none()
        return result

    @classmethod
    def name_from_id(cls, item_id: int) -> Optional[MusicBrainzEntity.name]:
        """
        Get the name of a MusicBrainzEntity from its database ID.

        Args:
            item_id (int): The ID of the MusicBrainzEntity to get the name of.

        Returns:
            Optional[MusicBrainzEntity.name]: The name (str) of the MusicBrainzEntity, or None if no entry with the specified ID is found.
        """
        if not isinstance(item_id, int) or item_id <= 0:
            return None
        result = app_db.session.query(cls.name).where(cls.id == item_id).one_or_none()
        return result[0] if result is not None else None

    @classmethod
    def id_by_matching_name(cls, name: str) -> list[MusicBrainzEntity.id]:
        """
        Get all MusicBrainzEntity IDs of a given type (Release, Artist, Label) where the name matches the `name` argument.

        Args:
            name (str): The name to match on.

        Returns:
            list[MusicBrainzEntity.id]: A list of MusicBrainzEntity IDs (int) with names that match the `name` argument.
        """
        if not isinstance(name, str):
            return []
        result = app_db.session.query(cls.id).filter(cls.name.ilike(f'%{name}%')).all()
        # .all() returns a list of tuples like [(1,), (2,)] so return list comprehension unpacks it to [1, 2]
        return [r[0] for r in result]

class Release(MusicBrainzEntity):
    __tablename__ = "release"
    artist_id: Mapped[int] = mapped_column(ForeignKey("artist.id"))
    label_id: Mapped[int] = mapped_column(ForeignKey("label.id"))
    release_year: Mapped[int] = mapped_column(Integer())
    runtime: Mapped[int] = mapped_column(Integer())
    rating: Mapped[int] = mapped_column(Integer())
    listen_date: Mapped[datetime] = mapped_column(DateTime())
    track_count: Mapped[int] = mapped_column(Integer())
    country: Mapped[str] = mapped_column(String())
    genre: Mapped[str] = mapped_column(String())
    tags: Mapped[str | None] = mapped_column(String())

    tag_list = relationship("Tag", back_populates="release", cascade="all, delete-orphan")
    reviews = relationship("Review", cascade="all, delete-orphan", back_populates="release")
    # Below is deprecated; can be removed, but need to deal with existing entries
    review: Mapped[str | None] = mapped_column(String())

    def __init__(self, mbid: str | None = None, artist_id: int = 0, label_id: int = 0, **kwargs):
        super().__init__()
        self.mbid = mbid
        self.artist_id = artist_id
        self.label_id = label_id
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def average_runtime(cls) -> float:
        """
        Calculate the average runtime of all Release entries.

        Returns:
            float: The average runtime of all Release entries, rounded to 2 decimal places. If there are no Release entries, returns 0.
        """
        try:
            avg_runtime_ms = app_db.session.query(func.avg(cls.runtime)).scalar()
            avg_runtime_min = avg_runtime_ms / 60000
            result = round(avg_runtime_min, 2)
        except TypeError:
            result = 0
        except Exception as e:
            raise e
        return result

    @classmethod
    def total_runtime(cls) -> float:
        """
        Calculate the total runtime of all Release entries.

        Returns:
            float: The total runtime of all Release entries, rounded to 2 decimal places. If there are no Release entries, returns 0.
        """
        try:
            total_runtime_ms = app_db.session.query(func.sum(cls.runtime)).scalar()
            total_runtime_hours = total_runtime_ms / 3600000
            result = round(total_runtime_hours, 2)
        except TypeError:
            result = 0
        return result

    @classmethod
    def ratings_lowest(cls, limit: int = 10) -> list[Release | None]:
        """
        Return a list of the lowest rated releases, up to the specified limit.

        Args:
            limit (int, optional): The maximum number of releases to return. If not provided, the default is 10. Must be a positive integer.

        Returns:
            list[Release | None]: A list of Release objects, ordered by rating in ascending order.

        Raises:
            ValueError: If the `limit` parameter is not a positive integer.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")
        result = (app_db.session.query(
            cls.id,
            cls.name,
            cls.rating,
            cls.artist_id,
            cls.label_id
        ).limit(limit).order_by(cls.rating.asc()).all())
        return result


    @classmethod
    def ratings_highest(cls, limit: int = 10) -> list[Release | None]:
        """
        Return a list of the highest rated releases, up to the specified limit.

        Args:
            limit (int, optional): The maximum number of releases to return. If not provided, the default is 10. Must be a positive integer.

        Returns:
            list[Release | None]: A list of Release objects, ordered by rating in descending order.

        Raises:
            ValueError: If the `limit` parameter is not a positive integer.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")
        result = (
            app_db.session.query(
                cls.id,
                cls.name,
                cls.rating,
                cls.artist_id,
                cls.label_id
            ).limit(limit).order_by(cls.rating.desc()).all()
        )
        return result

    @classmethod
    def ratings_average(cls) -> float:
        """
        Retrieves the average rating for all releases.

        Returns:
            float: The average rating for all releases, rounded to 2 decimal places.
                   Returns 0.0 if no release exists or an exception is raised.
        """
        try:
            ratings = app_db.session.query(
                func.avg(cls.rating)
            ).scalar()
            result = round(ratings or 0, 2)
        except Exception as e:
            result = 0.0
        return result

    @classmethod
    def home_data(cls) -> list[Row]:
        """
        Retrieves a list of data for the home page, including artist information, release information, and associated tags.

        Returns:
            list[Row]: A list of database rows containing the following fields:
                - artist_id (int): The ID of the artist associated with the release.
                - artist_name (str): The name of the artist associated with the release.
                - id (int): The ID of the release.
                - name (str): The name of the release.
                - rating (float): The rating of the release.
                - listen_date (datetime): The date the release was listened to.
                - genre (str): The genre of the release.
                - image (str): The URL of the release's image.
                - tags (list[str]): A list of tags associated with the release.

        The data is ordered by the release ID in descending order.
        """
        results = (
            app_db.session.query(
                Artist.id.label('artist_id'),
                Artist.name.label('artist_name'),
                cls.id,
                cls.name,
                cls.rating,
                cls.listen_date,
                cls.genre,
                cls.image,
                func.array_agg(func.concat(Tag.name)).label('tags')
            )
            .join(Artist, Artist.id == cls.artist_id)
            .outerjoin(Tag, Tag.release_id == cls.id)
            .group_by(
                Artist.id,
                cls.id,
            )
            .order_by(cls.id.desc())
        ).all()
        return results

    @classmethod
    def listens_this_year(cls) -> int:
        """
        Counts the number of releases listened to during the current year.

        Returns:
            int: The total number of releases listened to during the current year. Returns 0 if an exception is encountered.
        """
        try:
            current_year = datetime.now().year
            results = app_db.session.query(
                func.count(Release.id)
            ).filter(
                extract('year', Release.listen_date) == current_year
            ).scalar()
        except Exception as e:
            return 0
        return results

    @classmethod
    def listens_per_day(cls) -> float:
        """
        Calculates the average number of listens per day so far this year.

        Returns:
            float: The average number of listens per day so far this year, rounded to 2 decimal places.
        """
        days_this_year: int = date.today().timetuple().tm_yday
        if days_this_year == 0:
            return 0.0
        total_listens_this_year = cls.listens_this_year()
        # Round to 2 decimals
        result = total_listens_this_year / days_this_year
        return round(result, 2)

    @classmethod
    def dynamic_search(
            cls,
            data: dict
    ) -> list[Release]:
        """
        Dynamically search for Release objects based on the provided search criteria.

        The search criteria is passed as a dictionary, where the keys represent the fields to
        filter on and the values represent the desired values for those fields. The function
        will construct a SQLAlchemy query based on the provided criteria and return a list
        of Release objects that match the search.

        The function supports the following search criteria:
        - label: Filter by the name of the label associated with the release.
        - artist: Filter by the name of the artist associated with the release.
        - rating: Filter by the rating of the release, using a comparison operator.
        - year: Filter by the year the release was listened to, using a comparison operator.
        - name: Filter by the name of the release, using a case-insensitive partial match.
        - tags: Filter by the tags associated with the release.

        Any other keys in the search criteria dictionary will be used to filter the query
        directly on the Release model attributes.

        Args:
            data (dict): A dictionary containing the search criteria.

        Returns:
            list[Release]: A list of Release objects representing the matching releases.

        Raises:
            ValueError: If `data` is not a dictionary.
        """
        if not isinstance(data, dict):
            raise ValueError("Search criteria must be a dictionary")
        from .util import apply_comparison_filter
        query = app_db.session.query(cls)
        search_keys = ["name", "artist", "country", "genre", "label", "rating", "tags", "release_year"]
        for key, value in data.items():
            if value == '' or value == [''] or key not in search_keys:
                pass # Empty value or key not meant for searching, do nothing
            elif key == 'name':
                query = query.filter(
                    cls.name.ilike(f'%{value}%')
                )
            elif key == 'artist':
                artist_ids = Artist.id_by_matching_name(name=value)
                query = query.filter(cls.artist_id.in_(artist_ids))
            elif key == 'label':
                label_ids = Label.id_by_matching_name(name=value)
                query = query.filter(cls.label_id.in_(label_ids))
            elif key == 'rating':
                operator = data["rating_comparison"]   # <, ==, or >
                query = apply_comparison_filter(
                    query=query,
                    model=cls,
                    key=key,
                    operator=operator,
                    value=value
                )
            elif key == 'release_year':
                operator = data["year_comparison"] # <, ==, or >
                query = apply_comparison_filter(
                    query=query,
                    model=cls,
                    key=key,
                    operator=operator,
                    value=value
                )
            elif key == 'tags':
                # Retrieve all tags related to the Release ID
                query = query.join(Tag, Tag.release_id == cls.id)
                # Filter to only show results with matching tag name
                for tag in value:
                    query = query.filter(Tag.name == tag)
            else:
                # generic handler for any other search key not matching above (country, genre)
                query = query.filter(
                    getattr(cls, key) == value
                )
        results = query.order_by(cls.id).all()
        return results

    @classmethod
    def get_reviews(
            cls,
            release_id: int,
    ) -> list[Row]:
        """
        Retrieves a list of reviews for the specified release ID.

        Args:
            release_id (int): The ID of the release to retrieve reviews for.

        Returns:
            list[Row]: A list of review objects, where each object contains the timestamp and text of the review.

        Raises:
            ValueError: If `release_id` is a non-integer or an integer less than 0.
        """
        if not isinstance(release_id, int) or release_id < 0:
            raise ValueError("Release ID must be a positive integer.")
        reviews = (
            app_db.session.query(
                func.to_char(Review.timestamp, 'YYYY-MM-DD HH24:MI').label('timestamp'),
                Review.text
            ).where(Review.release_id == release_id)
        ).all()
        return reviews

    @staticmethod
    def create_new(data: dict) -> int:
        """
        Creates a new release record in the database and retrieves the assigned ID.

        Args:
            data (dict): A dictionary containing the data for the new release, including the name, artist name, label name, and release group MBID.

        Returns:
            int: The ID of the newly created release.

        Raises:
            ValueError: If `data` is not a dictionary.
            Any exceptions that may be raised by the `construct_item`, `insert`, `update`, or `get_image` functions.
        """
        if not isinstance(data, dict):
            raise ValueError("data argument must be a dictionary")
        from .util import construct_item
        from .operations import insert, update
        from ..api import Util
        new_release = construct_item('release', data)
        release_id = insert(new_release)

        image_filepath = Util.get_image(
            item_type='release',
            item_id=release_id,
            release_name=data["name"],
            artist_name=data["artist_name"],
            label_name=data["label_name"],
            mbid=data["release_group_mbid"]
        )
        new_release.image = image_filepath
        update(new_release)
        return new_release.id

class ArtistOrLabel(MusicBrainzEntity):
    """
    Abstract base class for Artist and Label models with shared fields.

    Attributes:
        id: Primary key identifier
        mbid: Optional MusicBrainz ID
        name: Name of the artist/label
        country: Optional country of origin
        type: Optional type classification
        begin_date: Optional start date
        end_date: Optional end date
        image: Optional image file path
    """
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    mbid: Mapped[str | None] = mapped_column(String(), unique=True)
    name: Mapped[str] = mapped_column(String())
    country: Mapped[str | None] = mapped_column(String())
    type: Mapped[str | None] = mapped_column(String())
    begin_date: Mapped[date | None] = mapped_column(Date())
    end_date: Mapped[date | None] = mapped_column(Date())
    image: Mapped[str | None] = mapped_column(String())

    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, name='{self.name}')"

    @classmethod
    def frequency_highest(
            cls,
            limit: int = 10
    ) -> list[dict]:
        """
        Retrieve the top `limit` most frequently occurring Artists or Labels, along with the count of their associated Releases and their image file paths.

        This method is a class method, so it can be called on either the Artist or Label model classes.

        Args:
            limit (int): The maximum number of results to return, defaults to 10.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary contains the following keys:
                - "name": The name of the Artist or Label.
                - "count": The number of Releases associated with the Artist or Label.
                - "image": The file path of the image associated with the Artist or Label.

        Raises:
            ValueError: If `limit` is not a positive integer.
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")
        relation_id = Release.artist_id if cls.__tablename__ == "artist" else Release.label_id

        query = (
            app_db.session.query(
                cls.name,
                func.count(relation_id).label('count'),
                cls.image
            )
            .join(Release, relation_id == cls.id)
            # Disregard Artist/Label entries that are not related to a specific real-world entity
            .where(cls.name.notin_(["[NONE]", "Various Artists"]))
            .group_by(cls.name, cls.image)
            .order_by(func.count(relation_id).desc())
            .limit(limit)
            .all()
        )
        results = [
            {
                "name": result.name,
                "count": result.count,
                "image": result.image
            } for result in query
        ]
        return results

    @classmethod
    def average_ratings_and_total_counts(
            cls,
    ) -> list[Row]:
        """
        Calculates the average ratings and total release counts for entities (Artists or Labels) in the database.

        Returns:
            list[Row]: A list of database rows containing the following fields:
                - id: The unique identifier for the entity.
                - name: The name of the entity.
                - average_rating: The average rating for the entity's releases.
                - release_count: The total number of releases for the entity.
                - image: The file path of the image associated with the entity.

        Raises:
            TypeError: If the method is called on a class that is not either the Artist or Label class.
        """
        if cls.__tablename__ == "artist":
            relation_id = Release.artist_id
        elif cls.__tablename__ == "label":
            relation_id= Release.label_id
        else:
            raise TypeError("Method only supported by Artist and Label classes.")
        entities = (
            app_db.session.query(
                cls.id,
                cls.name,
                func.avg(Release.rating).label('average_rating'),
                func.count(Release.id).label('release_count'),
                cls.image
            )
            .join(Release, relation_id == cls.id)
            .where(cls.name.notin_(["[NONE]", "Various Artists"]))
            .having(func.count(Release.id) > 1)
            .group_by(cls.name, cls.id)
            .order_by(func.avg(Release.rating).desc())
            .all()
        )
        return entities

    @classmethod
    def average_ratings_bayesian(
            cls,
            sort_order: str = 'desc',
    ) -> list[dict]:
        """
        Calculates the Bayesian average rating for entities (Artists or Labels) in the database, taking into account both the average rating and the number of releases for each entity.

        The Bayesian average is calculated as a weighted average between the entity's average rating and the overall mean average rating, with the weight determined by the number of releases for that entity.

        Args:
            sort_order (str, optional): The order to sort the results, either 'desc' (descending) or 'asc' (ascending). Defaults to 'desc'.

        Returns:
            list[dict]: A list of dictionaries containing the following fields for each entity:
                - id: The unique identifier for the entity.
                - name: The name of the entity.
                - rating: The Bayesian average rating for the entity.
                - image: The file path of the image associated with the entity.
                - count: The total number of releases for the entity.

        Raises:
            ValueError: If the `sort_order` parameter is not 'desc' or 'asc'.
        """
        if not isinstance(sort_order, str) or sort_order not in ["desc", "asc"]:
            raise ValueError(f"Unrecognized sort order: {sort_order}. Valid orders are: 'desc', 'asc'")

        entities = cls.average_ratings_and_total_counts()
        # Calculate the mean average and mean length (i.e. average number of releases, and average of rating averages)
        entity_count = len(entities)
        if entity_count == 0:
            # If entities list has length 0, there are no releases in the database
            return []
        else:
            from .util import mean_avg_and_count, bayesian_avg
            mean_avg, mean_count = mean_avg_and_count(entities)
            items = []
            # Iterate through the entries and calculate their Bayesian averages
            for entity in entities:
                entity_avg = int(entity.average_rating)
                entity_count = int(entity.release_count)

                weight = entity_count / (entity_count + mean_count)
                bayesian = bayesian_avg(
                    item_weight=weight,
                    item_avg=entity_avg,
                    mean_avg=mean_avg
                )
                items.append({
                    "id": entity.id,
                    "name": entity.name,
                    "rating": round(bayesian),
                    "image": entity.image,
                    "count": entity.release_count
                })

            # Sort results by Bayesian average
            # 'order' is used for sorted(reverse=..)
            # Hence, order = True means descending; False means ascending
            order = True
            if sort_order == 'asc':
                order = False

            sorted_entities = sorted(
                items,
                key=lambda k: k['rating'],
                reverse=order
            )
            return sorted_entities

    @classmethod
    def statistic(
            cls,
            sort_order: str,
            metric: str,
            item_property: str
    ) -> list[dict]:
        # Currently unused
        """
        Search for a typical statistic, i.e. average rating, total count
        :param sort_order: 'desc' or 'asc'; determines the order to sort the results before return
        :param metric: The type of statistic to retrieve; 'average' or 'total'
        :param item_property: The property (column) to calculate the statistic of
        :return: Sorted list of dictionaries containing data related to the Artist/Label and the queried statistic
        """
        if sort_order not in ['asc', 'desc']:
            raise ValueError(f"Unrecognized sort order: {sort_order}. Valid orders are: 'desc', 'asc'")

        order = 'desc'
        if sort_order == 'lowest':
            order = 'asc'

        result = cls.average_ratings_and_total_counts()
        if metric == 'average':
            if item_property == 'rating':
                return sorted(result, key=lambda k: k['rating'], reverse=order)
            elif item_property == 'runtime':
                return sorted(result, key=lambda k: k['runtime'], reverse=order)

        elif metric == 'total':
            if item_property == 'count':
                return sorted(result, key=lambda k: k['count'], reverse=order)
            elif item_property == 'runtime':
                return sorted(result, key=lambda k: k['runtime'], reverse=order)

    @classmethod
    def dynamic_search(
            cls,
            filters: dict
    ) -> List[ArtistOrLabel]:
        """
        Perform a dynamic search on the database model represented by `cls`, using the provided `filters` dictionary.

        The `filters` dictionary can contain the following keys:
        - `name`: Perform a partial string match on the `name` column.
        - `begin_date`: Perform a comparison filter on the `begin_date` column, using the `begin_comparison` key to specify the comparison operator (`<`, `=`, or `>`).
        - `end_date`: Perform a comparison filter on the `end_date` column, using the `end_comparison` key to specify the comparison operator (`<`, `=`, or `>`).
        - Other keys: Filter the results where the column value matches the provided value.

        Returns:
            A list of model instances that match the provided filters.

        Raises:
            ValueError: If `filters` is not a dict
        """
        if not isinstance(filters, dict):
            raise ValueError("filters must be a dictionary")
        from .util import apply_comparison_filter
        query = app_db.session.query(cls)
        search_keys = ["name", "begin_date", "end_date", "country", "type"]
        for key, value in filters.items():
            if value == '' or key not in search_keys:
                pass # Empty value or key not meant from searching, pass
            elif key == 'name':
                query = query.filter(
                    cls.name.ilike(f'%{value}%')
                )
            elif key == 'begin_date':
                    operator = filters["begin_comparison"]
                    if operator not in ['<', '=', '>']:
                        raise ValueError(f"Unexpected operator value for begin_comparison: {operator}")
                    query = apply_comparison_filter(
                        query=query,
                        model=cls,
                        key=key,
                        operator=operator,
                        value=value
                    )
            elif key == 'end_date':
                    operator = filters["end_comparison"]
                    if operator not in ['<', '=', '>']:
                        raise ValueError(f"Unexpected operator value for end_comparison: {operator}")
                    query = apply_comparison_filter(
                        query=query,
                        model=cls,
                        key=key,
                        operator=operator,
                        value=value
                    )
            else:
                query = query.filter(
                    getattr(cls, key) == value
                )
        # Filter out names that do not refer to a specific real-world entity
        results = query.where(
            cls.name != "[NONE]"
        ).where(
            cls.name != "[no label]"
        ).where(
            cls.name != "Various Artists"
        ).all()
        return results

    @classmethod
    def create_if_not_exist(cls, mbid: str, name: str) -> int:
        """
        Create a new instance of the model if it does not already exist in the database.

        Args:
            mbid (str): The MusicBrainz ID of the item to create.
            name (str): The name of the item to create.

        Returns:
            int: The ID of the created or existing item.
        """
        from ..api import MusicBrainz, Util
        from .util import construct_item
        from .operations import insert
        item_exists = cls.exists_by_mbid(mbid)
        if item_exists:
            item_id = item_exists.id
        else:
            # Grab image, start/end date, type, and insert
            if cls.__name__ == 'Label':
                item_search = MusicBrainz.label_search(name=name, mbid=mbid)
                new_item = construct_item(model_name='label', data_dict=item_search)
            elif cls.__name__ == 'Artist':
                item_search = MusicBrainz.artist_search(name=name, mbid=mbid)
                new_item = construct_item(model_name='artist', data_dict=item_search)
            else:
                raise ValueError(f"Unsupported class: {cls} - supported classes are Label and Artist")

            item_id = insert(new_item)
            # TODO: see if Util.get_image() can be refactored; instead of label_name and artist_name use item_name
            if cls.__name__ == 'Label':
                Util.get_image(
                    item_type='label',
                    item_id=item_id,
                    label_name=name
            )
            elif cls.__name__ == 'Artist':
                Util.get_image(
                    item_type='artist',
                    item_id=item_id,
                    artist_name=name
                )
            # TODO: figure out a way to call Util.get_image() upon any insertion so it doesn't need to be manually called
        return item_id

class Label(ArtistOrLabel):
    __tablename__ = "label"

    @classmethod
    def get_releases(
            cls,
            label_id: int
    ) -> list[Row]:
        """
        Get all releases related to a given label_id
        :param label_id: Integer representing the Label's ID (primary key)
        :return: SQLAlchemy Row objects representing the releases related to the given label_id; empty list if none are found
        """
        releases = (
            app_db.session.query(Release, Artist)
            .join(Artist, Artist.id == Release.artist_id)
            .where(Release.label_id == label_id)
        ).all()
        return releases

class Artist(ArtistOrLabel):
    __tablename__ = "artist"

    @classmethod
    def get_releases(
            cls,
            artist_id: int
    ) -> list[Row]:
        """
        Get all releases related to a given artist_id
        :param artist_id: Integer representing the Artist's ID (primary key)
        :return: SQLAlchemy Row objects representing the releases related to the given artist_id; empty list if none are found
        """
        releases = (
            app_db.session.query(Release, Label.name, Label.id)
            .join(Label, Release.label_id == Label.id)
            .join(cls, cls.id == Release.artist_id)
            .where(cls.id == artist_id)
        ).all()
        return releases

class Goal(app_db.Model):
    __tablename__ = "goal"
    id: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[datetime] = mapped_column(DateTime())
    end_goal: Mapped[datetime] = mapped_column(DateTime())
    end_actual: Mapped[datetime | None] = mapped_column(DateTime())
    type: Mapped[str] = mapped_column(String()) # i.e. release, album, label
    amount: Mapped[int] = mapped_column(Integer())

    @property
    def new_releases_since_start_date(self):
        """
        Returns the count of releases that have a listen_date greater than or equal to the start_date of the Goal instance.
        This property is used to determine if the Goal has been met, based on the number of new releases since the Goal's start date.
        """
        return (
            app_db.session.query(func.count(Release.id))
            .filter(Release.listen_date >= self.start_date)
            .scalar()
        )

    def update_goal(self):
        """
        Updates the `end_actual` attribute of the `Goal` instance if the number of new releases since the goal's `start_date` is greater than or equal to the `amount` attribute.

        This method is used to check if a goal has been met, based on the number of new releases since the goal's start date. If the goal has been met, the `end_actual` attribute is updated to the current time.
        """
        print(f'Target amount: {self.amount} - Actual amount: {self.new_releases_since_start_date}')
        if self.type == 'release':
            if self.new_releases_since_start_date >= self.amount:
                print('Updating end_actual to current time')
                self.end_actual = datetime.now()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def get_incomplete(cls) -> list[Goal] | None:
        """
        Query database for goals without an end_actual date, meaning they have not been completed
        Returns a list of the goals if found; none otherwise
        """
        query = app_db.session.query(cls).where(cls.end_actual.is_(None))
        results = query.all()
        if results:
            return results
        else:
            return None

    @classmethod
    def check_goals(cls) -> None:
        """
        Checks all incomplete goals and updates them if the goal has been met.

        This method retrieves all incomplete goals from the database, then for each goal it calls the `update_goal()` method to check if the goal has been met based on the number of new releases since the goal's start date. If the goal has been met, the `end_actual` attribute is updated to the current time, and the updated goal is saved to the database.
        """
        active_goals = cls.get_incomplete()
        if active_goals is not None:
            for goal in active_goals:
                goal.update_goal()
                if goal.end_actual:
                    # Goal is complete; updating db entry
                    from .operations import update
                    update(goal)


class Review(app_db.Model):
    __tablename__ = "review"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("release.id"))
    timestamp: Mapped[date] = mapped_column(DateTime, default=func.now())
    text: Mapped[str] = mapped_column(String())

    release = relationship("Release", back_populates="reviews")


class Tag(app_db.Model):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("release.id"))
    name: Mapped[str] = mapped_column(String())

    release = relationship("Release", back_populates="tag_list")

    __table_args__ = (
        # Make sure release can't have multiple of the same tag
        UniqueConstraint('release_id', 'name', name='unique_release_tag'),
    )


    @staticmethod
    def create_tags(tags: str, release_id: int) -> None:
        """
        Create tags for a given release in the database.

        Args:
            tags (str): A comma-separated string of tag names to create.
            release_id (int): The ID of the release to associate the tags with.

        This function splits the `tags` string on commas to get a list of individual tag names.
        For each tag name, it constructs a new `Tag` object with the tag name and the given `release_id`,
        and inserts the new tag into the database using the `insert` function from the `operations` module.
        """
        from .util import construct_item
        from .operations import insert
        for tag in tags.split(','):
            tag_data = {"name": tag, "release_id": release_id}
            tag_obj = construct_item('tag', tag_data)
            insert(tag_obj)
