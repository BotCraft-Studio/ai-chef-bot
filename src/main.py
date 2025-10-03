import logging

import psycopg
from dotenv import load_dotenv

load_dotenv()

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from src.db import storage_new
from src.config import BOT_TOKEN
from src.handlers import on_text, on_callback, on_photo
from src.handlers.command_handler import (
    daily_cmd,
    del_cmd,
    help_cmd,
    list_cmd,
    premium_cmd,
    profile_cmd,
    start_cmd,
    privacy_cmd
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_app() -> Application:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("premium", premium_cmd))
    application.add_handler(CommandHandler("profile", profile_cmd))
    application.add_handler(CommandHandler("list", list_cmd))
    application.add_handler(CommandHandler("del", del_cmd))
    application.add_handler(CommandHandler("daily", daily_cmd))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    application.add_handler(MessageHandler(filters.PHOTO, on_photo))
    application.add_handler(CommandHandler("privacy", privacy_cmd))

    return application


if __name__ == "__main__":
    # Проверить соединение с БД
    try:
        storage_new.get_connection().close()
        logger.info("Проверка соединения с БД на этапе инициализации успешно пройдена")
    except psycopg.Error as e:
        logger.error("Возникла ошибка во время попытки открыть соединение с БД:", exc_info=True)
        raise e

    app = build_app()
    # Запустить бота
    app.run_polling(allowed_updates=None)
