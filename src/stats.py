from models import app_db, Release, Artist, Label, Tag
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
    return top_rated_entities(Label)


def top_rated_artists():
    return top_rated_entities(Artist)


def top_rated_entities(model: app_db.Model,
                       sort_order: str = 'desc'):
    if model == Artist:
        join_id = Release.artist_id
    elif model == Label:
        join_id = Release.label_id
    else:
        raise ValueError(f'Unknown entity type: {model}')

    if join_id:
        entities = (
            app_db.session.query(
                model.id,
                model.name,
                func.avg(Release.rating).label('average_rating'),
                func.count(Release.id).label('release_count'),
                model.image
        )
            .join(Release, join_id == model.id)
            .where(model.name != "[NONE]")
            .having(func.count(Release.id) > 1)
            .group_by(model.name, model.id).all())
        # Calculate the mean average and mean length (i.e. average number of releases, and average of rating averages)
        avg_sum = 0
        len_sum = 0
        for entity in entities:
            avg_sum += int(entity[2])
            len_sum += int(entity[3])
        mean_avg = avg_sum / len(entities)
        mean_len = len_sum / len(entities)
        items = []
        for entity in entities:
            entity_avg = int(entity[2])
            entity_len = int(entity[3])

            entity_weight = entity_len / (entity_len + mean_len)
            bayesian = bayesian_avg(entity_weight, entity_avg, mean_avg)

            item = {"data": entity, "bayesian": bayesian}
            items.append(item)

        order = True
        if sort_order == 'asc':
            order = False
        sorted_entities = sorted(items, key=lambda k: k['bayesian'], reverse=order)
        top_entities = []
        # Parse into a more usable dictionary format
        for i in sorted_entities[0:10]:
            top_entities.append({
                "id": i["data"][0],
                "name": i["data"][1],
                "rating": round(i["bayesian"]),
                "image": i["data"][4],
                "count": i["data"][3]
            })
        return top_entities


def top_frequent_labels():
    query = (
        app_db.session.query(
            Label.name,
            func.count(Release.label_id).label('count'),
            Label.image
        )
        .join(Release, Release.label_id == Label.id)
        .where(Label.name != "[NONE]")
        .group_by(Label.name, Label.image)
        .order_by(func.count(Release.label_id).desc())
        .limit(10)
        .all()
    )
    results = [
        {
            "name": result.name,
            "count": result.count,
            "image": result.image
        } for result in query]
    return results


def top_frequent_artists():
    query = (
        app_db.session.query(
            Artist.name,
            func.count(Release.artist_id).label('count'),
            Artist.image
        )
        .join(Release, Release.artist_id == Artist.id)
        # Exclude "Various Artists"
        .where(Artist.name != "Various Artists")
        .group_by(Artist.name, Artist.image)
        .order_by(func.count(Release.artist_id).desc())
        .limit(10)
        .all()
    )
    results = [
        {
            "name": result.name,
            "count": result.count,
            "image": result.image
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
            func.array_agg(func.concat(Tag.name)).label('tags')
        )
        .join(Artist, Artist.id == Release.artist_id)
        .outerjoin(Tag, Tag.release_id == Release.id)
        .group_by(
            Artist.id,
            Release.id,
        )
        .order_by(Release.id.desc())
    ).all()
    return results


def bayesian_avg(item_weight, item_avg, mean_avg):
    return item_weight * item_avg + (1 - item_weight) * mean_avg


