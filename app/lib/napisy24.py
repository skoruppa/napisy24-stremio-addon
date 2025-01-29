import requests
import io
import re
from app.routes.utils import cache
import xml.etree.ElementTree as ET

NAPISY24_API_USER = "subliminal"
NAPISY24_API_PASSWORD = "lanimilbus"


class Napisy24API:
    """
    Napisy24 API wrapper
    """
    _cache = {}
    _cache_expiry = 600  # 10 mi

    def __init__(self):
        """
        Initialize the Napisy24 API wrapper
        """

    @staticmethod
    @cache.memoize()
    def fetch_subtitles_from_hash(filehash: str, filesize: str, filename: str):
        url = "http://napisy24.pl/run/CheckSubAgent.php"
        payload = {
            'postAction': 'CheckSub',
            'ua': NAPISY24_API_USER,
            'ap': NAPISY24_API_PASSWORD,
            'fh': filehash,
            'fs': filesize,
            'n24pref': 1
        }
        if filename:
            payload['fn'] = filename
        headers = {"User-Agent": "Subliminal", "Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Błąd: {response.status_code}")

        response_content = response.content.split(b'||', 1)
        response_text = response_content[0].decode()
        if response_text.startswith("OK-2"):
            fps = float(re.search(r"fps:([\d.]+)", response_text).group(1))
            sub_id = float(re.search(r"lp:([\d.]+)", response_text).group(1))
            return response_text, io.BytesIO(response_content[-1]), fps, sub_id
        return None, None, None, None

    @staticmethod
    def fetch_subtitles_from_imdb_id(imdbId, filename=None):
        parts = imdbId.split(':')
        if len(parts) > 1:
            return []  # Napis24 uses individual episodes imdb id that I can't easily map

        url = f"http://napisy24.pl/libs/webapi.php?imdb={imdbId}"
        response = requests.get(url)

        if response.status_code != 200 or response.text == 'brak wynikow':
            return []

        subtitles = []
        response_text = response.text.strip()

        # Wyszukaj deklarację XML i usuń ją z reszty tekstu
        xml_decl_match = re.match(r"<\?xml.*?\?>", response_text)
        if xml_decl_match:
            response_text = response_text[xml_decl_match.end():].strip()

        # Dodaj poprawny root
        response_text = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<subtitles>{response_text}</subtitles>"

        # Parsowanie XML
        root = ET.fromstring(response_text)

        for subtitle in root.findall("subtitle"):
            sub_id = subtitle.find("id").text
            fps = float(subtitle.find("fps").text)
            release = subtitle.find("release").text

            if filename is None or (release and filename[:-4] in release):
                subtitles.append({
                    'id': sub_id,
                    'fps': fps,
                    'release': release
                })

        return subtitles

    @staticmethod
    def download_subtitle_id(subtitle_id: str):
        url = f"http://napisy24.pl/run/pages/download.php?napisId={subtitle_id}"
        headers = {"Referer": "http://napisy24.pl/"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return None

        return io.BytesIO(response.content)
