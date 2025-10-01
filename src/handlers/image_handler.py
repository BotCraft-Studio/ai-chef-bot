"""
Модуль отвечает за обработку изображений, поступающих от пользователя
"""
import io
from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from providers.gigachat import GigaChatVision
from handlers.base import normalize_items, render_precheck      # уже есть в base.py
from keyboards import goal_choice_menu
from utils.bot_utils import SESSION_ITEMS, APPEND_MODE, AWAIT_MANUAL

vision = GigaChatVision()

async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_chat.send_message("📥 Фото получено, обрабатываю…")
    # 1) самое большое превью
    photo = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)

    # 2) скачиваем и слегка уменьшаем (ускоряет распознавание)
    raw = io.BytesIO()
    await tg_file.download_to_memory(out=raw)
    img = Image.open(io.BytesIO(raw.getvalue())).convert("RGB")

    out = io.BytesIO()
    img.thumbnail((1280, 1280))
    img.save(out, format="JPEG", quality=85)
    image_bytes = out.getvalue()

    # 3) распознаём продукты Яндексом
    try:
        detected = await vision.parse_ingredients(image_bytes)
    except Exception as e:
        return await update.message.reply_text(
            f"😕 Не удалось обработать фото: {e}\n"
            "Попробуйте другое фото (светлый фон, продукты крупно) или введите список текстом."
        )
    
    # временный лог в чат (потом удалишь):
    await update.effective_chat.send_message(f"🔎 Обнаружено: {', '.join(detected) or '— пусто —'}")

    if not detected:
        return await update.message.reply_text(
            "Не получилось распознать продукты на фото. "
            "Попробуйте другое фото или введите текстом."
        )

    # 4) нормализуем и кладём в СЕССИЮ (как «чистый лист»)
    norm = normalize_items(detected)
    if not norm:
        return await update.message.reply_text(
            "Не получилось распознать продукты на фото. "
            "Попробуйте другое фото (светлый фон, продукты крупно) или введите текстом."
        )

    context.user_data[SESSION_ITEMS] = norm
    context.user_data[APPEND_MODE] = False
    context.user_data[AWAIT_MANUAL] = False

    # 5) показываем пречек + выбор цели (та же функция, что в текстовом вводе)
    precheck = render_precheck(norm, highlights=set(), updated=False)
    await update.message.reply_text(
        precheck,
        reply_markup=goal_choice_menu(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
