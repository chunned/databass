from flask import Blueprint, render_template, request
from .. import db

label_bp = Blueprint(
    'label_bp', __name__,
    template_folder='templates'
)


@label_bp.route('/label/<string:label_id>', methods=['GET'])
def label(label_id):
    label_data = db.exists(item_type='label', item_id=label_id)
    label_releases = db.get_label_releases(label_id)
    data = {"label": label_data, "releases": label_releases}
    return render_template('label.html', data=data)

@label_bp.route('/labels', methods=["GET"])
def labels():
    countries = db.get_distinct_col(db.Label, 'country')
    types = db.get_distinct_col(db.Label, 'type')
    data = {"countries": countries, "types": types}
    return render_template('labels.html', data=data, active_page='labels')

@label_bp.route('/label/<string:label_id>', methods=['GET', 'POST'])
def edit_label(label_id):
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        pass