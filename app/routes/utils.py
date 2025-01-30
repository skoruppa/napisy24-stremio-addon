import logging
from io import BytesIO

from flask import jsonify, flash, make_response, url_for, redirect, Response, send_file
from flask_caching import Cache
cache = Cache()


def handle_error(err) -> Response:
    """
    Handles errors from MyAnimeList's API
    """
    if 400 >= err.response.status_code < 500:
        flash(err, "danger")
        return make_response(redirect(url_for('index')))
    elif err.response.status_code >= 500:
        log_error(err)
        flash(err, "danger")
        return make_response(redirect(url_for('index')))


def log_error(err):
    """
    Logs errors from MyAnimeList's API
    """
    response = err.response.json()
    error_label = response.get('error', 'No error label in response').capitalize()
    message = response.get('message', 'No message field in response')
    hint = response.get('hint', 'No hint field in response')
    logging.error(f"{error_label} [{err.response.status_code}] -> {message}\n HINT: {hint}\n")


# Enable CORS
def respond_with(data) -> Response:
    """
    Respond with CORS headers to the client
    """
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp


def return_srt_file(data, filename) -> Response:
    if not data:
        return make_response("No data to return", 400)

    buffer = BytesIO()
    buffer.write(data.encode("utf-8"))
    buffer.seek(0)

    resp = make_response(buffer.getvalue())
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}.srt"
    resp.headers["Content-Type"] = "application/x-subrip"
    resp.headers["Content-Length"] = str(len(data.encode("utf-8")))

    return resp
