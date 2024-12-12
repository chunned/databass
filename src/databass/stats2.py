
# def search(sort_order: str,
#            metric: str,
#            item_type: str,
#            item_property: str):
#     order = 'desc'
#     if sort_order == 'lowest':
#         order = 'asc'
#
#     model = get_model(item_type)
#
#     result = ratings_and_counts(model)
#     if metric == 'average':
#         if item_property == 'rating':
#             return sorted(result, key=lambda k: k['rating'], reverse=order)
#         elif item_property == 'runtime':
#             return sorted(result, key=lambda k: k['runtime'], reverse=order)
#
#     elif metric == 'total':
#         if item_property == 'count':
#             return sorted(result, key=lambda k: k['count'], reverse=order)
#         elif item_property == 'runtime':
#             return sorted(result, key=lambda k: k['runtime'], reverse=order)
#
#
# def ratings_and_counts(
#         model: app_db.Model,
# ):
#     # Calculates the average rating and total count for existing entries related to the input model
#     if model == Artist:
#         join_id = Release.artist_id
#     elif model == Label:
#         join_id = Release.label_id
#     else:
#         raise ValueError(f'Unknown entity type: {model}')
#     if join_id:
#         entities = (
#             app_db.session.query(
#                 model.id,
#                 model.name,
#                 func.avg(Release.rating).label('average_rating'),
#                 func.count(Release.id).label('release_count'),
#                 func.sum(Release.runtime).label('total_runtime'),
#                 func.avg(Release.runtime).label('average_runtime')
#             )
#             .join(Release, join_id == model.id)
#             .where(model.name != "[NONE]")
#             .group_by(model.name, model.id)
#         ).all()
#         return entities
#
#
# def favourite_items(
#         sort_order: str,
#         model: app_db.Model
# ):
#     # Calculates the Bayesian average of existing entries
#     averages = ratings_and_counts('desc', model)
#     mean_average, mean_length = mean_avg_and_len(averages)
#     # Iterate through list items, calculate weight and Bayesian average
#     items = []
#     for item in averages:
#         item_avg = int(item[2])
#         item_len = int(item[3])
#         weight = item_len / (item_len / mean_length)
#         bayesian = weight * item_avg + (1 - weight) * mean_average
#         # Parse into more usable dictionary format
#         new_item = {
#             "id": item[0],
#             "name": item[1],
#             "rating": round(bayesian),
#             "count":  item[3]
#         }
#         items.append(new_item)
#     # By default, order will be descending
#     order = True
#     if sort_order == 'asc':
#         order = False
#     return sorted(items, key=lambda k: k['bayesian'], reverse=order)
#
#
# def mean_avg_and_len(averages: list):
#     # Input: List outputted by average_ratings()
#     # Calculates mean average and length for the input list
#     avg = length = 0
#     total = len(averages)
#     for item in averages:
#         avg += int(item[2])
#         length += int(item[3])
#     mean_avg = avg / total
#     mean_len = length / total
#     return mean_avg, mean_len
