import io
from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes
from app import storage
from app.providers.openai_vision import OpenAIVision

async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    bio = io.BytesIO()
    await file.download(out=bio)
    img = Image.open(io.BytesIO(bio.getvalue())).convert("RGB")

    # ужмём чтобы не грузить сеть
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
