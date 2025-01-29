import logging

from flask import Flask, render_template, session, url_for, redirect
from flask_compress import Compress
from app.routes.subtitles import subtitles_bp
from app.routes.manifest import manifest_blueprint
from app.routes.utils import cache
from config import Config

app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.config.from_object('config.Config')
app.register_blueprint(manifest_blueprint)
app.register_blueprint(subtitles_bp)

Compress(app)
cache.init_app(app)

logging.basicConfig(format='%(asctime)s %(message)s')


@app.route('/')
@app.route('/configure')
def index():
    """
    Render the index page
    """
    manifest_url = f'{Config.PROTOCOL}://{Config.REDIRECT_URL}/manifest.json'
    manifest_magnet = f'stremio://{Config.REDIRECT_URL}/manifest.json'
    return render_template('index.html', logged_in=True,
                               manifest_url=manifest_url, manifest_magnet=manifest_magnet)


@app.route('/favicon.ico')
def favicon():
    """
    Render the favicon for the app
    """
    return app.send_static_file('favicon.ico')


@app.route('/callback')
def callback():
    """
    Callback URL from MyAnimeList
    :return: A webpage response with the manifest URL and Magnet URL
    """
    return redirect(url_for('index'))


if __name__ == '__main__':
    from waitress import serve

    serve(app, host='0.0.0.0', port=5000)

