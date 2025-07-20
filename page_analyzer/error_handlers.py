from flask import render_template


def page_not_found(error):
    return render_template('errors/404.html'), 404


def server_error(error):
    return render_template('errors/500.html'), 500


def register_error_handlers(app):
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, server_error)