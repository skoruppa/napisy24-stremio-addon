from flask import Blueprint
from .utils import respond_with

manifest_blueprint = Blueprint('manifest', __name__)

MANIFEST = {
    'id': 'com.skoruppa.napisy24-stremio-addon',
    'version': '0.0.1',
    'name': 'Napisy24 Addon',
    'logo': 'https://napisy24.pl/templates/st_magazine/favicon.ico',
    'description': 'Addon for getting subtitles from Napisy24.pl',
    'types': ['movie', 'series'],
    'catalogs': [],
    'contactEmail': 'skoruppa@gmail.com',
    'behaviorHints': {'configurable': False},
    'resources': ['subtitles']
}


@manifest_blueprint.route('/manifest.json')
def addon_manifest():
    """
    Provides the manifest for the addon after the user has authenticated with MyAnimeList
    :return: JSON response
    """
    return respond_with(MANIFEST)
