import requests
import io
import re
import xml.etree.ElementTree as ET
from app.routes.utils import cache

NAPISY24_API_USER = "subliminal"
NAPISY24_API_PASSWORD = "lanimilbus"


class Napisy24API:
    @staticmethod
    @cache.memoize(timeout=600)
    def fetch_subtitles_from_hash(filehash: str, filesize: str, filename: str):
        response = requests.post("http://napisy24.pl/run/CheckSubAgent.php", data={
            'postAction': 'CheckSub', 'ua': NAPISY24_API_USER, 'ap': NAPISY24_API_PASSWORD,
            'fh': filehash, 'fs': filesize, 'n24pref': 1, 'fn': filename or ""
        }, headers={"User-Agent": "Subliminal"})

        if response.status_code != 200:
            return None, None, None, None

        response_text, response_data = response.content.split(b'||', 1)
        if not response_text.startswith(b"OK-2"):
            return None, None, None, None

        fps = float(re.search(rb"fps:([\d.]+)", response_text).group(1))
        sub_id = int(re.search(rb"lp:([\d.]+)", response_text).group(1))
        return response_text.decode(), io.BytesIO(response_data), fps, sub_id

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
