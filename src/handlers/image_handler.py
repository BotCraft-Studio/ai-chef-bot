"""
Модуль отвечает за обработку изображений, поступающих от пользователя
"""

from telegram import Update
from telegram.ext import ContextTypes


# from app.providers.openai_vision import OpenAIVision  # ← ЗАКОММЕНТИРУЙТЕ

async def on_photo(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # Временная заглушка для фото
    await update.message.reply_text(
        "📷 Фото получено! Функция распознавания продуктов временно недоступна.\n\n"
        "Пожалуйста, введите продукты текстом через запятую."
    )

    # Старый код (закомментирован)
    """
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    bio = io.BytesIO()
    await file.download(out=bio)
    img = Image.open(io.BytesIO(bio.getvalue())).convert("RGB")

    out = io.BytesIO()
    img.thumbnail((1280, 1280))
    img.save(out, format="JPEG", quality=85)

    ai = OpenAIVision()
    ingredients = await ai.parse_ingredients(out.getvalue())
    if not ingredients:
        return await update.message.reply_text("Не удалось распознать продукты. Попробуйте другое фото.")

    storage.add_ingredients(update.effective_user.id, ingredients)
    reply = await ai.recipe_with_macros(ingredients)
    await update.message.reply_text("📋 Распознано: " + ", ".join(ingredients) + "\n\n" + reply)
    """
