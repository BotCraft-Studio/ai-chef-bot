import logging

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from db import storage_new
from handlers import on_photo
from src import storage
from src.config import BOT_TOKEN
from src.handlers import on_text, on_callback
from src.handlers.command_handler import (
    daily_cmd,
    del_cmd,
    help_cmd,
    list_cmd,
    premium_cmd,
    profile_cmd,
    start_cmd
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


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

    return application


if __name__ == "__main__":
    # Проверить соединение с БД
    storage_new.get_connection().close()
    storage.init_db()
    app = build_app()
    # Запустить бота
    app.run_polling(allowed_updates=None)


