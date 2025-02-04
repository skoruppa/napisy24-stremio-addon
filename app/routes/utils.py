from io import BytesIO
from flask import jsonify, make_response, Response
from flask_caching import Cache

cache = Cache()


def respond_with(data) -> Response:
    resp = jsonify(data)
    resp.headers['Access-Control-Allow-Origin'] = "*"
    resp.headers['Access-Control-Allow-Headers'] = '*'
    return resp


def return_srt_file(data, filename) -> Response:
    if not data:
        return make_response("No data to return", 400)

    buffer = BytesIO(data.encode("utf-8"))
    resp = make_response(buffer.getvalue())
    resp.headers.update({
        "Content-Disposition": f"attachment; filename={filename}.srt",
        "Content-Type": "application/x-subrip",
        "Content-Length": str(len(data.encode("utf-8")))
    })
    return resp
