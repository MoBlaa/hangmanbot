"""Settings"""

import os
from dotenv import load_dotenv
from appdirs import user_data_dir

load_dotenv()

APP_NAME = "HangmanBot"
APP_AUTHOR = "Mo Blaa"
DISCORD_TOKEN = os.getenv("TOKEN")
CONFIG_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
STATES_FILE = os.path.join(CONFIG_DIR, ".states.json")

if not DISCORD_TOKEN:
    raise RuntimeError("TOKEN EnvVar required (or .env)")
