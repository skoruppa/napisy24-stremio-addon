from lxml import etree
import requests
import io
import re
import xml.etree.ElementTree as ET
from themoviedb import TMDb
from app.routes.utils import cache
from config import Config


TMDB_KEY = Config.TMDB_KEY
NAPISY24_API_USER = "subliminal"
NAPISY24_API_PASSWORD = "lanimilbus"

tmdb = TMDb(key=TMDB_KEY, language="pl-PL", region="PL")


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

        match = re.search(rb"fps:([\d.]+)", response_text)
        fps = float(match.group(1)) if match else None
        sub_id = int(re.search(rb"lp:([\d.]+)", response_text).group(1))
        return response_text.decode(), io.BytesIO(response_data), fps, sub_id

    @staticmethod
    def fetch_subtitles_from_imdb_id(imdbId, filename=None):
        parts = imdbId.split(':')
        season = None
        episode = None
        if len(parts) > 1:
            new_id = parts[0]
            tmdb_data = tmdb.find().by_imdb(new_id).tv_results[0]
            tmdb_id = tmdb_data.id
            if len(parts) == 3:
                season = int(parts[1])
                episode = int(parts[2])
            else:
                episode = int(parts[1])
                season = 1
            imdbId = tmdb.episode(tmdb_id, season, episode).external_ids().imdb_id

        url = f"http://napisy24.pl/libs/webapi.php?imdb={imdbId}"
        response = requests.get(url)

        if response.status_code != 200 or response.text == 'brak wynikow':
            episode_string = f' {season}x{episode}'
            if not episode:
                episode_string = ''
                tmdb_data = tmdb.find().by_imdb(imdbId).movie_results[0]
                name = tmdb_data.title
            else:
                name = tmdb_data.name
            url = f"https://napisy24.pl/libs/webapi.php?title={name}{episode_string}"
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
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = ET.fromstring(response_text, parser=parser, )

        for subtitle in root.findall("subtitle"):
            sub_id = subtitle.find("id").text
            try:
                fps = float(subtitle.find("fps").text.replace(",", "."))
            except (AttributeError, ValueError):
                fps = None
            release = subtitle.find("release").text

            sub_item = {
                    'id': sub_id,
                    'fps': fps,
                    'release': release
                }

            if filename and release in filename[:-4]:
                return [sub_item]

            subtitles.append(sub_item)

        return subtitles

    @staticmethod
    def download_subtitle_id(subtitle_id: str):
        url = f"http://napisy24.pl/run/pages/download.php?napisId={subtitle_id}"
        headers = {"Referer": "http://napisy24.pl/"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return None

        return io.BytesIO(response.content)
