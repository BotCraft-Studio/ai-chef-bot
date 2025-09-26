import os
from dotenv import load_dotenv

load_dotenv()

# TELEGRAM BOT
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required in .env")
RUN_MODE = os.getenv("RUN_MODE", "polling")  # polling | webhook

# YANDEX API
USE_YANDEX = os.getenv("USE_YANDEX", "0").lower() in ("1", "true", "yes")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
YANDEX_TIMEOUT = int(os.getenv("YANDEX_TIMEOUT", "45"))

# DATABASE
ENABLE_MIGRATIONS = os.getenv("ENABLE_MIGRATIONS", "false").lower()
