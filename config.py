import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

REMNAWAVE_API_TOKEN = os.getenv("REMNAWAVE_API_TOKEN")

REMNAWAVE_FRONTEND_URL = os.getenv("REMNAWAVE_FRONTEND_URL")

DATABASE_URL = os.getenv("DATABASE_URL")
