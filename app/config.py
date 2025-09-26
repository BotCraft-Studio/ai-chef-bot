import os
from dotenv import load_dotenv

load_dotenv()

# TELEGRAM BOT
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required in .env")
RUN_MODE = os.getenv("RUN_MODE", "polling")  # polling | webhook

# YANDEX API
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
YANDEX_TIMEOUT = int(os.getenv("YANDEX_TIMEOUT", "45"))

# DATABASE
DB_URI = os.getenv("DB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bsc")
ENABLE_MIGRATIONS = os.getenv("ENABLE_MIGRATIONS", "0").lower() not in ("1", True, False)
MIGRATIONS_FOLDER = os.getenv("MIGRATIONS_FOLDER", "migrations")
MIGRATIONS_LOG_COLLECTION = os.getenv("MIGRATIONS_LOG_COLLECTION", "database_migrations")
