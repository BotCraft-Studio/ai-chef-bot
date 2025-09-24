import os
from dotenv import load_dotenv

load_dotenv()

# --- YANDEX settings (new)
BOT_TOKEN = os.getenv("BOT_TOKEN")
RUN_MODE = os.getenv("RUN_MODE", "polling")   # polling | webhook
TZ = os.getenv("TZ", "Europe/Amsterdam")

USE_YANDEX = os.getenv("USE_YANDEX", "0").lower() in ("1", "true", "yes")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")
YANDEX_TIMEOUT = int(os.getenv("YANDEX_TIMEOUT", "45"))

WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
PORT = int(os.getenv("PORT", "8080"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required in .env")