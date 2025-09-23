import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.config import BOT_TOKEN, RUN_MODE, WEBHOOK_HOST, WEBHOOK_PATH, PORT
from app import storage
from app.handlers import start, help_cmd, list_cmd, del_cmd, daily_cmd, on_text, on_photo, on_callback

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

async def _setup(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("del", del_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

async def polling():
    storage.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    await _setup(app)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=None)
    await app.updater.wait()

# --- webhook через FastAPI (на потом) ---
from fastapi import FastAPI, Request
from telegram import Update
import uvicorn

app_fastapi = FastAPI()
app_tg: Application | None = None

@app_fastapi.on_event("startup")
async def _on_start():
    global app_tg
    if RUN_MODE != "webhook":
        return
    storage.init_db()
    app_tg = Application.builder().token(BOT_TOKEN).build()
    await _setup(app_tg)
    await app_tg.initialize()
    await app_tg.bot.set_webhook(url=f"{WEBHOOK_HOST}{WEBHOOK_PATH}")
    await app_tg.start()

@app_fastapi.on_event("shutdown")
async def _on_stop():
    global app_tg
    if app_tg:
        await app_tg.stop()

@app_fastapi.post(WEBHOOK_PATH)
async def webhook(request: Request):
    if not app_tg:
        return {"ok": False}
    data = await request.json()
    update = Update.de_json(data, app_tg.bot)
    await app_tg.process_update(update)
    return {"ok": True}

if __name__ == "__main__":
    if RUN_MODE == "webhook":
        uvicorn.run("app.main:app_fastapi", host="0.0.0.0", port=PORT, reload=False)
    else:
        asyncio.run(polling())
