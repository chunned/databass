from flask import Blueprint, render_template, request, redirect

error_bp = Blueprint(
    'error_bp', __name__,
    template_folder='templates'
)

# TODO: make error handlers use the generic error.html template
@error_bp.errorhandler(405)
def method_not_allowed(e):
    data = {
        "method": request.method,
        "arguments": request.args,
        "url": request.url,
        "data": request.data,
        "error_full": e.description,
        "valid_methods": e.valid_methods
    }
    return render_template('errors/405.html', data=data), 405


@error_bp.errorhandler(404)
def not_found(e):
    data = {
        "method": request.method,
        "arguments": request.args,
        "url": request.url,
        "data": request.data,
        "error_full": e.description,
    }
    return render_template('errors/404.html', data=data), 404


@error_bp.errorhandler(415)
def unsupported_media_type(e):
    data = {
        "method": request.method,
        "arguments": request.args,
        "url": request.url,
        "data": request.data,
        "error_full": e.description,
    }
    return render_template('errors/415.html', data=data), 415
