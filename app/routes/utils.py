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
    temp_file_path = "/tmp/test.srt"

    # Write a static file
    with open(temp_file_path, "w") as temp_file:
        temp_file.write(data)

    # Serve the file
    return send_file(
        temp_file_path,
        as_attachment=False,
        download_name="test.srt",
        mimetype="application/x-subrip"
    )