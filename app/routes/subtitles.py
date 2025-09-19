import base64
import json
from flask import Blueprint, url_for, Response, make_response, request, current_app
from urllib.parse import parse_qs, unquote

from app.routes import napisy24_client
from app.routes.utils import respond_with, return_srt_file
from app.lib.subtitles import extract_and_convert

subtitles_bp = Blueprint('subtitles', __name__)


@subtitles_bp.route('/subtitles/<content_type>/<content_id>/<params>.json')
@subtitles_bp.route('/subtitles/<content_type>/<content_id>/<path:params>')
def addon_stream(content_type: str, content_id: str, params: str):
    content_id = unquote(content_id)
    handling_error_file = request.query_string.decode()
    if handling_error_file:
        params = handling_error_file
    parsed_params = {k: v[0] for k, v in parse_qs(params).items() if v}

    if all(key in parsed_params for key in ("videoSize", "videoHash")):
        response, zipfile, fps, sub_id = napisy24_client.fetch_subtitles_from_hash(
            filehash=parsed_params["videoHash"],
            filename=parsed_params.get("filename"),
            filesize=parsed_params["videoSize"]
        )
        if response:
            encoded_params = base64.urlsafe_b64encode(json.dumps(parsed_params).encode()).decode()
            download_url = url_for('subtitles.download_subtitles_from_hash', params=encoded_params, _external=True)
            return respond_with(
                {'subtitles': [{'id': str(sub_id), 'url': download_url, 'SubEncoding': 'UTF-8', 'lang': 'pol'}]})

    if 'tt' in content_id:
        subtitles = {'subtitles': []}
        for subtitle in napisy24_client.fetch_subtitles_from_imdb_id(content_id, parsed_params.get("filename")):
            encoded_params = base64.urlsafe_b64encode(json.dumps(subtitle).encode()).decode()
            download_url = url_for('subtitles.download_subtitles_from_id', params=encoded_params, _external=True, _scheme=current_app.config['PROTOCOL'])
            subtitles['subtitles'].append({'id': str(subtitle['id']), 'url': download_url, 'SubEncoding': 'UTF-8',
                                           'lang': f'Napisy24: {subtitle["release"]}'})
        return respond_with(subtitles)

    return respond_with({'subtitles': []})


@subtitles_bp.route('/download/hash/<params>.srt')
def download_subtitles_from_hash(params: str):
    try:
        decoded_params = json.loads(base64.urlsafe_b64decode(params).decode())
        response, zipfile, fps, _ = napisy24_client.fetch_subtitles_from_hash(
            filehash=decoded_params["videoHash"],
            filename=decoded_params.get("filename"),
            filesize=decoded_params["videoSize"]
        )
        if zipfile:
            return return_srt_file(extract_and_convert(zipfile, fps), params)
    except Exception as e:
        return respond_with({"error": str(e)})


@subtitles_bp.route('/download/id/<params>.srt')
def download_subtitles_from_id(params: str):
    try:
        decoded_params = json.loads(base64.urlsafe_b64decode(params).decode())
        zipfile = napisy24_client.download_subtitle_id(subtitle_id=decoded_params["id"])
        if zipfile:
            return return_srt_file(extract_and_convert(zipfile, decoded_params["fps"]), params)
    except Exception as e:
        return respond_with({"error": str(e)})
