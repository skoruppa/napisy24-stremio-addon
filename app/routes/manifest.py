from flask import Blueprint
from .utils import respond_with

manifest_blueprint = Blueprint('manifest', __name__)

MANIFEST = {
    'id': 'com.skoruppa.napisy24-stremio-addon',
    'version': '0.0.4',
    'name': 'Napisy24 Addon',
    'logo': 'https://napisy24.pl/templates/st_magazine/favicon.ico',
    'description': 'Addon for getting polish subtitles from Napisy24.pl',
    'types': ['movie', 'series'],
    'catalogs': [],
    'contactEmail': 'skoruppa@gmail.com',
    'behaviorHints': {'configurable': False},
    'resources': ['subtitles'],
    'stremioAddonsConfig': {
        'issuer': 'https://stremio-addons.net',
        'signature': 'eyJhbGciOiJkaXIiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2In0..KjXNLdeZoDuNu5tcszX3Vg.dQrcQ7znHPiHQT7LyiOG-rsO0qRWItcIMZ33T71RnV-Ba5kQmDvyFL1jF9oHYKPvRjMIlXDbeUzVpadOtGKr87IWL_dkRNEpEXf0YK25JBE.zveN6jTFWtGa52zoTXtdNg'
    }
}


@manifest_blueprint.route('/manifest.json')
def addon_manifest():
    """
    Provides the manifest for the addon after the user has authenticated with MyAnimeList
    :return: JSON response
    """
    return respond_with(MANIFEST)
