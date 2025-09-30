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

# GIGACHAT
GIGACHAT_BASE_URL = os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1")
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID", "")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET", "")
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
GIGACHAT_TEXT_MODEL = os.getenv("GIGACHAT_TEXT_MODEL", "GigaChat")
GIGACHAT_VISION_MODEL = os.getenv("GIGACHAT_VISION_MODEL", "GigaChat-Pro")
GIGACHAT_VERIFY_SSL = os.getenv("GIGACHAT_VERIFY_SSL", "1") not in ("0", "false", "False")
