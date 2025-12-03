import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class
    """
    FLASK_HOST = os.getenv('FLASK_RUN_HOST', "localhost")
    FLASK_PORT = os.getenv('FLASK_RUN_PORT', "5000")
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 600
    TMDB_KEY = os.getenv('TMDB_KEY', "")

    DEBUG = os.getenv('FLASK_DEBUG', False)
    
    # Gunicorn/Waitress config
    WORKERS = int(os.getenv('WORKERS', 4))
    THREADS = int(os.getenv('THREADS', 2))

    # Env dependent configs
    if DEBUG in ["1", True, "True"]:  # Local development
        PROTOCOL = "http"
        REDIRECT_URL = f"{FLASK_HOST}:{FLASK_PORT}"
    else:  # Production environment
        PROTOCOL = "https"
        REDIRECT_URL = f"{FLASK_HOST}"