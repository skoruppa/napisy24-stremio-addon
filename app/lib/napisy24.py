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

        try:
            response_text, response_data = response.content.split(b'||', 1)
        except ValueError:
            print(f'unknown error: {response.content}')
            return None, None, None, None
        if not response_text.startswith(b"OK-2"):
            return None, None, None, None

        match = re.search(rb"fps:([\d.]+)", response_text)
        fps = float(match.group(1)) if match else None
        sub_id = int(re.search(rb"lp:([\d.]+)", response_text).group(1))
        return response_text.decode(), io.BytesIO(response_data), fps, sub_id

    @staticmethod
    def fetch_subtitles_from_imdb_id(imdbId, filename=None):
        if not imdbId.startswith("tt"):
            return []
        parts = imdbId.split(':')
        season = ''
        episode = ''
        search_string = None
        if len(parts) > 1:
            imdbId = parts[0]
            if len(parts) == 3:
                season = int(parts[1])
                episode = int(parts[2])
            else:
                episode = int(parts[1])
                season = 1

        url = f"http://napisy24.pl/libs/webapi.php?imdb={imdbId}"
        response = requests.get(url)

        if response.status_code != 200 or response.text == 'brak wynikow' or episode:
            try:
                if episode:
                    tmdb_data = tmdb.find().by_imdb(imdbId).tv_results[0]
                    episode_string = f' {season}x{episode:02}'
                    name = tmdb_data.name
                    original_name = tmdb_data.original_name
                else:
                    tmdb_data = tmdb.find().by_imdb(imdbId).movie_results[0]
                    episode_string = ''
                    name = tmdb_data.title
                    original_name = tmdb_data.original_title
            except (IndexError, ValueError):
                return []

            search_string = f'{name}{episode_string}'
            url = f"https://napisy24.pl/libs/webapi.php?title={search_string}"
            response = requests.get(url)
            if response.status_code != 200 or response.text == 'brak wynikow':
                search_string = f'{original_name}{episode_string}'
                url = f"https://napisy24.pl/libs/webapi.php?title={search_string}"
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
        response_text = response_text.replace('<br>', '')

        # Parsowanie XML
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = ET.fromstring(response_text, parser=parser, )

        for subtitle in root.findall("subtitle"):
            test = etree.tostring(subtitle, pretty_print=True, encoding='unicode')
            sub_id = subtitle.find("id").text
            try:
                fps = float(subtitle.find("fps").text.replace(",", "."))
            except (AttributeError, ValueError):
                fps = None
            release_el = subtitle.find("release")
            if release_el is not None:
                release = release_el.text
            else:
                release = 'unknown'
            title = subtitle.find("title").text
            altTitle = subtitle.find("altTitle").text or ''
            subSeason = subtitle.find("season")
            subSeason = subSeason.text if subSeason is not None else ''
            subEpisode = subtitle.find("episode")
            subEpisode = subEpisode.text if subEpisode is not None else ''

            sub_item = {
                    'id': sub_id,
                    'fps': fps,
                    'release': release
                }

            if filename and release and release in filename[:-4]:
                return [sub_item]

            if search_string:
                if search_string.lower() == title.lower() or search_string.lower() == altTitle.lower():
                    subtitles.append(sub_item)
            elif episode:
                if subSeason:
                    if int(subSeason) == season and int(subEpisode) == episode:
                        subtitles.append(sub_item)
            else:
                subtitles.append(sub_item)

        return subtitles

    @staticmethod
    def download_subtitle_id(subtitle_id: str):
        url = f"http://napisy24.pl/run/pages/download.php?napisId={subtitle_id}&typ=sr"
        headers = {"Referer": "http://napisy24.pl/"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return None

        return io.BytesIO(response.content)
