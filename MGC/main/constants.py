from pathlib import Path

# Project Constants

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT/ "data" / "gymData.db"
PORT = 5001
TEMPLATE_PATH = f'{ROOT}/templates'
STATIC_PATH = f'{ROOT}/static'
INIT_NUM_RANDOM_GOALS = 7
TARGET_URL = "https://emsenterprise.uic.edu/vrecems/BrowseEvents.aspx"
DAYS_TO_SEARCH = 4
SCRAPER_WAIT_TIME_SECONDS = 1
SCRAPER_STARTED = False
MUSIC_PATH = "../music/motivation.mp3"
SEED = 102938012983021832019

