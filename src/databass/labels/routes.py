from flask import Blueprint, render_template, request, flash, redirect
from .. import db
from ..db.models import Label

label_bp = Blueprint(
    'label_bp', __name__,
    template_folder='templates'
)


@label_bp.route('/label/<int:label_id>', methods=['GET'])
def label(label_id):
    if label_id == 0:
        return redirect("/")
    label_data = Label.exists_by_id(label_id)
    if not label_data:
        error = f"No label with ID {label_id} found."
        flash(error)
        return redirect('/error', code=302)
    label_releases = Label.get_releases(label_id)
    data = {"label": label_data, "releases": label_releases}
    return render_template('label.html', data=data)

@label_bp.route('/labels', methods=["GET"])
def labels():
    countries = Label.get_distinct_column_values('country')
    types = Label.get_distinct_column_values('type')
    data = {"countries": countries, "types": types}
    return render_template('labels.html', data=data, active_page='labels')

@label_bp.route('/label_search', methods=["POST"])
def label_search():
    from ..pagination import Pager
    data = request.get_json()
    search_results = Label.dynamic_search(data)
    page = Pager.get_page_param(request)
    paged_data, flask_pagination = Pager.paginate(
        per_page=15,
        current_page=page,
        data=search_results
    )
    return render_template(
        'label_search.html',
        data=paged_data,
        data_full=search_results,
        pagination=flask_pagination
    )

# TODO: implement edit_label
# @label_bp.route('/label/<string:label_id>', methods=['GET', 'POST'])
# def edit_label(label_id):
#     if request.method == 'GET':
#         pass
#     elif request.method == 'POST':
#         pass
# TODO: implement delete_label