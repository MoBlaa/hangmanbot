from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("TOKEN")
DISCORD_DISPLAY_NAME = os.getenv("USERNAME")