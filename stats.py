from models import app_db, Release, Artist, Label
from sqlalchemy import func, extract
from datetime import datetime, date


def get_all():
    # Calls all the other functions in this file, other than get_homepage_releases()
    stats = {
        "total_listens": total_releases(),
        "total_artists": total_artists(),
        "total_labels": total_labels(),
        "average_rating": average_rating(),
        "average_runtime": average_runtime(),
        "total_runtime": total_runtime(),
        "listens_this_year": listens_this_year(),
        "listens_per_day": listens_per_day(),
        "top_rated_labels": top_rated_labels(),
        "top_rated_artists": top_rated_artists(),
        "top_frequent_labels": top_frequent_labels(),
        "top_frequent_artists": top_frequent_artists()
    }
    return stats


def total_releases():
    results = app_db.session.query(Release).count()
    return results


def total_artists():
    results = app_db.session.query(Artist).count()
    return results


def total_labels():
    results = app_db.session.query(Label).count()
    return results


def average_rating():
    results = app_db.session.query(
        func.round(
            func.avg(Release.rating), 2
        )
    ).scalar()
    return results


def average_runtime():
    results = round(
        (
            (
                app_db.session.query(
                    func.avg(Release.runtime)
                ).scalar()) / 60000  # Convert ms to minutes
        ), 2  # Round to 2 decimals
    )
    return results


def total_runtime():
    results = round(
        (
            (
                app_db.session.query(func.sum(Release.runtime))
                .scalar()
            ) / 3600000  # Convert ms to hours
        ), 2  # Round to 2 decimals
    )
    return results


def listens_this_year():
    current_year = datetime.now().year
    results = app_db.session.query(
        func.count(Release.id)
    ).filter(
        extract('year', Release.listen_date) == current_year
    ).scalar()
    return results


def listens_per_day():
    days_this_year = date.today().timetuple().tm_yday
    total_this_year = listens_this_year()
    results = round((total_this_year / days_this_year), 2)
    return results


def top_rated_labels():
    query = (
        app_db.session.query(
            Label.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.label_id).label('release_count')
        )
        .join(Release, Release.label_id == Label.id)
        # Exclude non-real labels
        .filter(Label.name.notin_(['none', '[no label]']))
        # Exclude labels with only 1 release
        .group_by(Label.name)
        .having(func.count(Release.label_id) != 1)
        # Order by average release rating, rounded to 2 decimals
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        # Limit to 10 results
        .limit(10)
        .all()
    )
    results = [
        {
            "name": result.name,
            "average_rating": result.average_rating,
            "release_count": result.release_count
        } for result in query]
    return results


def top_rated_artists():
    query = (
        app_db.session.query(
            Artist.name,
            func.round(func.avg(Release.rating), 2).label('average_rating'),
            func.count(Release.artist_id).label('release_count')
        )
        .join(Release, Release.artist_id == Artist.id)
        .group_by(Artist.name)
        # Exclude artists with only 1 release
        .having(func.count(Release.artist_id) != 1)
        # Order by average release rating, rounded to 2 decimals
        .order_by(func.round(func.avg(Release.rating), 2).desc())
        # Limit to 10 results
        .limit(10)
        .all()
    )
    results = [
        {
            "name": result.name,
            "average_rating": result.average_rating,
            "release_count": result.release_count
        } for result in query]
    return results


def top_frequent_labels():
    query = (
        app_db.session.query(
            Label.name,
            func.count(Release.label_id).label('count')
        )
        .join(Release, Release.label_id == Label.id)
        .group_by(Label.name)
        .order_by(func.count(Release.label_id).desc())
        .limit(10)
        .all()
    )
    results = [
        {
            "name": result.name,
            "count": result.count
        } for result in query]
    return results


def top_frequent_artists():
    query = (
        app_db.session.query(
            Artist.name,
            func.count(Release.artist_id).label('count')
        )
        .join(Release, Release.artist_id == Artist.id)
        # Exclude "Various Artists"
        .where(Artist.name != "Various Artists")
        .group_by(Artist.name)
        .order_by(func.count(Release.artist_id).desc())
        .limit(10)
        .all()
    )
    results = [
        {
            "name": result.name,
            "count": result.count
        } for result in query]

    return results


def get_homepage_releases():
    results = (
        app_db.session.query(
            Artist.id.label('artist_id'),
            Artist.name.label('artist_name'),
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
    return results
