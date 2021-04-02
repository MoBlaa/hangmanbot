from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_TOKEN = os.getenv("TOKEN")

if not DISCORD_TOKEN:
    raise RuntimeError("Bot is required a Discord TOKEN environment variable (or a .env file) to login")
