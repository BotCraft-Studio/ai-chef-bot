import logging

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from app import storage
from app.config import BOT_TOKEN, ENABLE_MIGRATIONS
from app.db import migration_runner
from app.handlers import (
    start, help_cmd, list_cmd, del_cmd, daily_cmd, on_text, on_callback, premium_cmd, profile_cmd
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def build_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("premium", premium_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


if __name__ == "__main__":
    migration_runner.manage_migrations(ENABLE_MIGRATIONS)
    storage.init_db()
    app = build_app()
    app.run_polling(allowed_updates=None)
