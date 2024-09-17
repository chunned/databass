from flask import Blueprint, render_template, request
from flask_paginate import Pagination, get_page_parameter
from ..db import get_incomplete_goals
from ..api import Util
from ..stats import get_all as get_stats, get_homepage_releases as get_releases
from datetime import datetime


home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@home_bp.route('/', methods=['GET'])
@home_bp.route('/home', methods=['GET'])
def home():
    stats_data = get_stats()
    active_goals = get_incomplete_goals()
    goal_data = []
    for goal in active_goals:
        start_date = goal.start_date
        end_goal = goal.end_goal
        goal_type = goal.type
        amount = goal.amount

        current = goal.new_releases_since_start_date
        remaining = amount - current
        days_left = (end_goal - datetime.today()).days
        progress = round((current / amount) * 100)
        target = round(remaining / days_left)
        goal_data.append({
            "start_date": start_date,
            "end_goal": end_goal,
            "type": goal_type,
            "amount": amount,
            "progress": progress,
            "target": target,
            "current": current
        })

    data = get_releases()
    page = request.args.get(
        get_page_parameter(),
        type=int,
        default=1
    )
    per_page = 5
    start, end = Util.get_page_range(per_page, page)

    paged_data = data[start:end]

    flask_pagination = Pagination(
        page=page,
        total=len(data),
        search=False,
        record_name='latest_releases'
    )

    return render_template(
        'index.html',
        data=paged_data,
        stats=stats_data,
        goals=goal_data,
        pagination=flask_pagination,
        active_page='home'
    )
