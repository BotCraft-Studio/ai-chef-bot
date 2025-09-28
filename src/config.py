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
YANDEX_API_URL = os.getenv("YANDEX_API_URL", "https://llm.api.cloud.yandex.net/foundationModels/v1/completion")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
YANDEX_TIMEOUT = int(os.getenv("YANDEX_TIMEOUT", "45"))

# DATABASE
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "bcs")
DB_USER = os.getenv("DB_USER", "bcs")
DB_PASSWORD = os.getenv("DB_PASSWORD", "bcs")
DB_ENABLE_MIGRATIONS = os.getenv("ENABLE_MIGRATIONS", "0").lower() not in ("1", True, False)
