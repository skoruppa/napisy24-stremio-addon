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
REQUEST_TIMEOUT = 5

tmdb = TMDb(key=TMDB_KEY, language="pl-PL", region="PL")
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=1)
session.mount('http://', adapter)
session.mount('https://', adapter)


class Napisy24API:
    @staticmethod
    @cache.memoize(timeout=600)
    def fetch_subtitles_from_hash(filehash: str, filesize: str, filename: str):
        try:
            response = session.post("http://napisy24.pl/run/CheckSubAgent.php", data={
                'postAction': 'CheckSub', 'ua': NAPISY24_API_USER, 'ap': NAPISY24_API_PASSWORD,
                'fh': filehash, 'fs': filesize, 'n24pref': 1, 'fn': filename or ""
            }, headers={"User-Agent": "Subliminal"}, timeout=REQUEST_TIMEOUT)
        except (requests.Timeout, requests.ConnectionError):
            return None, None, None, None

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
    @cache.memoize(timeout=600)
    def fetch_subtitles_from_imdb_id(imdbId, filename=None):
        if not imdbId.startswith("tt"):
            return []
        parts = imdbId.split(':')
        season = None
        episode = None
        if len(parts) > 1:
            imdbId = parts[0]
            if len(parts) == 3:
                season = int(parts[1])
                episode = int(parts[2])
            else:
                episode = int(parts[1])
                season = 1

        all_subtitles = {}
        
        # Pobierz dane z TMDB
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
            name = None
            original_name = None
            episode_string = ''

        # Zbierz napisy z wszystkich źródeł
        urls_to_check = [f"http://napisy24.pl/libs/webapi.php?imdb={imdbId}"]
        
        if name:
            urls_to_check.append(f"https://napisy24.pl/libs/webapi.php?title={name}{episode_string}")
        if original_name and original_name != name:
            urls_to_check.append(f"https://napisy24.pl/libs/webapi.php?title={original_name}{episode_string}")

        for url in urls_to_check:
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT)
                if response.status_code != 200 or response.text == 'brak wynikow':
                    continue
            except (requests.Timeout, requests.ConnectionError):
                continue

            response_text = response.text.strip()
            xml_decl_match = re.match(r"<\?xml.*?\?>", response_text)
            if xml_decl_match:
                response_text = response_text[xml_decl_match.end():].strip()

            response_text = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<subtitles>{response_text}</subtitles>"
            response_text = response_text.replace('<br>', '')

            parser = etree.XMLParser(recover=True, encoding='utf-8')
            try:
                root = ET.fromstring(response_text, parser=parser)
            except ET.ParseError:
                continue

            for subtitle in root.findall("subtitle"):
                sub_id = subtitle.find("id").text
                if sub_id in all_subtitles:
                    continue

                try:
                    fps = float(subtitle.find("fps").text.replace(",", "."))
                except (AttributeError, ValueError):
                    fps = None
                release_el = subtitle.find("release")
                release = release_el.text if release_el is not None else 'unknown'
                author_el = subtitle.find("author")
                author = author_el.text if author_el is not None and author_el.text else None

                subSeason = subtitle.find("season")
                subSeason = int(subSeason.text) if subSeason is not None and subSeason.text else None
                subEpisode = subtitle.find("episode")
                subEpisode = int(subEpisode.text) if subEpisode is not None and subEpisode.text else None

                # Filtruj po sezonie/odcinku
                if episode is not None:
                    if subSeason is not None and season is not None and subSeason != season:
                        continue
                    if subEpisode is not None and subEpisode != episode:
                        continue

                sub_item = {
                    'id': sub_id,
                    'fps': fps,
                    'release': release,
                    'author': author
                }

                if filename and release and release in filename[:-4]:
                    return [sub_item]

                all_subtitles[sub_id] = sub_item

        return list(all_subtitles.values())

    @staticmethod
    @cache.memoize(timeout=3600)
    def download_subtitle_id(subtitle_id: str):
        url = f"http://napisy24.pl/run/pages/download.php?napisId={subtitle_id}&typ=sr"
        headers = {"Referer": "http://napisy24.pl/"}
        try:
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                return None
            return io.BytesIO(response.content)
        except (requests.Timeout, requests.ConnectionError):
            return None
