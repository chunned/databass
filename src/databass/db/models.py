from __future__ import annotations
from sqlalchemy import String, Integer, ForeignKey, DateTime, Date, func, UniqueConstraint, extract, distinct
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, date
from sqlalchemy.engine.row import Row

from .base import app_db

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True)

    @classmethod
    def get_all(cls) -> list:
        # Return all database entries for this class
        results = app_db.session.query(cls).all()
        return results

    @classmethod
    def total_count(cls) -> int:
        # Return the count of all database entries for this class
        try:
            results = app_db.session.query(cls).count()
            if results is None:
                return 0
            elif isinstance(results, int):
                return results
            else:
                raise TypeError(f"Expected int, got {type(results)}: {results}")
        except Exception as e:
            raise e

    @classmethod
    def exists_by_id(
            cls,
            item_id: int
    ) -> Base | False:
        """
        Check if an item exists in the database by its ID
        :param item_id: Item's ID (primary key)
        :return: The item, if it exists, or False if the item does not exist
        """
        result = app_db.session.query(cls).filter(cls.id == item_id).one_or_none()
        if result:
            return result
        else:
            return False

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
            result = app_db.session.query(
                distinct(attribute)
            ).all()
            values = [i[0] for i in result]
            return values
        except AttributeError as e:
            raise e

class MusicBrainzEntity(Base):
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
    ) -> MusicBrainzEntity | False:
        """
        Check if an item exists in the database by its MusicBrainzID (mbid)
        :param mbid: Item's MusicBrainzID
        :return: The item, if it exists, or False if the item does not exist
        """
        result = app_db.session.query(cls).filter(cls.mbid == mbid).one_or_none()
        if result:
            return result
        else:
            return False

    @classmethod
    def exists_by_name(
            cls,
            name: str
    ) -> MusicBrainzEntity | False:
        """
        Check if an item exists in the database by its name
        :param name: The item's name
        :return: The item, if it exists, or False if the item does not exist
        """
        result = app_db.session.query(cls).filter(cls.name.ilike(f'%{name}%')).one_or_none()
        if result:
            return result
        else:
            return False


app_db.Model = Base


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
    def average_runtime(cls) -> list[float]:
        """
        Calculate the average rating for all releases
        :return: list of floats representing each Release runtime in minutes, rounded to 2 decimals
        """
        try:
            results = round(
                (
                        (
                            app_db.session.query(
                                func.avg(cls.runtime)
                            ).scalar()) / 60000  # Convert ms to minutes
                ), 2  # Round to 2 decimals
            )
        except TypeError:
            results = 0
        except Exception as e:
            raise e
        return results

    @classmethod
    def total_runtime(cls) -> float:
        """
        Calculate the total runtime (sum of runtime for every Release entry)
        :return: Float rounded to 2 decimals representing the total runtime in hours
        """
        try:
            results = round(
                (
                        (
                            app_db.session.query(func.sum(cls.runtime))
                            .scalar()
                        ) / 3600000  # Convert ms to hours
                ), 2  # Round to 2 decimals
            )
        except TypeError:
            results = 0
        return results

    @classmethod
    def ratings_lowest(cls, limit: int = None) -> list[Release | None]:
        """
        Return a list of the lowest rated releases
        :param limit: Integer representing the maximum number of releases to return
        :return: List of Release objects
        """
        result = (app_db.session.query(
            cls.rating
        ).limit(
            limit
        ).order_by(
            cls.rating.asc()
        ).all())
        return result

    @classmethod
    def ratings_highest(cls, limit: int = None) -> list[Release | None]:
        """
        Return a list of the highest rated releases
        :param limit: Integer representing the maximum number of releases to return
        :return: List of Release objects
        """
        result = (
            app_db.session.query(
                cls.rating
            ).limit(
                limit
            ).order_by(
                cls.rating.desc()
            ).all()
        )
        return result

    @classmethod
    def ratings_average(cls) -> float:
        results = app_db.session.query(
            func.round(
                func.avg(cls.rating), 2
            )
        ).scalar()
        return results

    @classmethod
    def home_data(cls) -> list[Row]:
        """
        Retrieve release data to be shown on homepage (/, /index)
        :return: List of Row objects containing Release and Artist data
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
        Retrieves all Release entries where listen_date year is equal to current year and counts them
        :return: Integer representing the number of releases listened to this year
        """
        current_year = datetime.now().year
        results = app_db.session.query(
            func.count(Release.id)
        ).filter(
            extract('year', Release.listen_date) == current_year
        ).scalar()
        return results

    @classmethod
    def listens_per_day(cls) -> float:
        """
        Counts the number of releases listened to, per day, for the current year
        :return: Float representing the number of releases listened to per day for the current year
        """
        days_this_year = date.today().timetuple().tm_yday
        total_listens_this_year = cls.listens_this_year()
        # Round to 2 decimals
        results = round(
            (total_listens_this_year / days_this_year), 2
        )
        return results

    @classmethod
    def dynamic_search(
            cls,
            data: dict
    ) -> list[Row]:
        from .util import apply_comparison_filter
        query = app_db.session.query()
        for key, value in data.items():
            if 'comparison' in key or key == 'qtype':
                # Utility field, not a query field
                pass
            elif value == '' or value == 'NO VALUE':
                # No value for the given key
                pass
            else:
                if key == 'label':
                    label = Label.exists_by_name(name=value)
                    label_id = [l.id for l in label]
                    query = query.filter(cls.label_id.in_(label_id))
                elif key == 'artist':
                    artist = Artist.exists_by_name(name=value)
                    artist_id = [a.id for a in artist]
                    query = query.filter(cls.artist_id.in_(artist_id))
                elif key == 'rating':
                    # operator denotes the type of comparison to make; <, =, or >
                    operator = data["rating_comparison"]
                    query = apply_comparison_filter(
                        query=query,
                        model=cls,
                        key=key,
                        operator=operator,
                        value=value
                    )
                elif key == 'year':
                    # operator denotes the type of comparison to make; <, =, or >
                    operator = data["year_comparison"]
                    query = apply_comparison_filter(
                        query=query,
                        model=cls,
                        key=key,
                        operator=operator,
                        value=value
                    )
                elif key == 'name':
                    query = query.filter(
                        cls.name.ilike(f'%{value}%')
                    )
                elif key == 'tags':
                    # Retrieve all tags related to the Release ID
                    query = query.join(Tag, Tag.release_id == cls.id)
                    # Filter to only show results with matching tag name
                    for tag in value:
                        query = query.filter(Tag.name == tag)
                else:
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
        Retrieve the reviews related to the Release calling this function
        :param release_id: Integer representing Release's ID (primary key) in the database
        :return: List of SQLAlchemy Row objects containing the review time and text for all reviews related to the release object
        """
        reviews = (
            app_db.session.query(
                func.to_char(Review.timestamp, 'YYYY-MM-DD HH24:MI').label('timestamp'),
                Review.text
            ).where(Review.release_id == release_id)
        ).all()
        return reviews


class ArtistOrLabel(MusicBrainzEntity):
    # Artist and Label tables are both built from this prototype
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)
    mbid: Mapped[str | None] = mapped_column(String(), unique=True)
    name: Mapped[str] = mapped_column(String())
    country: Mapped[str | None] = mapped_column(String())
    type: Mapped[str | None] = mapped_column(String())
    begin_date: Mapped[date | None] = mapped_column(Date())
    end_date: Mapped[date | None] = mapped_column(Date())
    image: Mapped[str | None] = mapped_column(String())

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def frequency_highest(
            cls,
            limit: int = 10
    ) -> list[dict]:
        """
        Returns a list of the most frequent labels/artists based on number of Release entries with a relation to the label/artist
        Relation ID is the foreign key for the Release to match on - Release.artist_id if this is an Artist class, Release.label_id otherwise
        :param limit: Integer representing the maximum number of objects to return
        :return: List of dictionaries; each dict contains artist/label name, release count, and image
        """
        relation_id = Release.artist_id if cls.__tablename__ == "artist" else Release.label_id

        query = (
            app_db.session.query(
                cls.name,
                func.count(relation_id).label('count'),
                cls.image
            )
            .join(Release, relation_id == cls.id)
            # Disregard Artist/Label entries that are not related to a specific real-world entity
            .where(cls.name not in ["[NONE]", "Various Artists"])
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
        Retrieve all average ratings and total counts of releases per Artist/Label
        :param limit: Integer representing the maximum number of objects to return
        :return: Unordered list of Row objects containing data related to the Artist/Label and its average rating and total release count
        """
        if cls.__tablename__ == "artist":
            relation_id = Release.artist_id
        elif cls.__tablename__ == "label":
            relation_id = Release.label_id
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
            .where(cls.name not in ["[NONE]", "Various Artists"])
            .having(func.count(Release.id) > 1)
            .group_by(cls.name, cls.id)
            .all()
        )
        return entities

    @classmethod
    def average_ratings_bayesian(
            cls,
            sort_order: str = 'desc',
    ) -> list[dict]:
        """
        Calculates the Bayesian averages for database entries
        :param sort_order: 'desc' or 'asc'; determines the order to sort the results before return
        :param limit: Integer representing the maximum number of objects to return
        :return: Ordered list of dictionaries containing data related to the Artist/Label and its average Bayesian rating
        """
        if sort_order not in ["desc", "asc"]:
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
    ) -> list:
        """
        Handles querying/filtering database entries based on any available field
        :param filters: Dictionary of values to filter by
        :return: List of matching results
        """
        from .util import apply_comparison_filter
        query = app_db.session.query()
        for key, value in filters.items():
            if 'comparison' in key or key == 'qtype':
                # Utility field, not a query field
                pass
            elif value == '' or value == 'NO VALUE':
                # No value for the given key
                pass
            else:
                if key == 'name':
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
            app_db.session.query(Release, Label.name)
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
        return (
            app_db.session.query(func.count(Release.id))
            .filter(Release.listen_date >= self.start_date)
            .scalar()
        )

    def check_and_update_goal(self):
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


class Review(app_db.Model):
    __tablename__ = "review"
    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[int] = mapped_column(ForeignKey("release.id"))
    timestamp: Mapped[date] = mapped_column(DateTime, default=func.now())
    text: Mapped[str] = mapped_column(String())


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



