from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.keyboards import main_menu
from app import storage
from app.providers.yandex_vision import YandexRecipes
recipes = YandexRecipes()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage.upsert_user(update.effective_user.id)
    await update.message.reply_text(
        "Привет! Я ваш личный повар 👨‍🍳.\n\n"
        "Пришлите фото продуктов — распознаю и предложу рецепт с КБЖУ.\n"
        "Команды: /help, /daily 09:00 on|off, /list, /del",
        reply_markup=main_menu()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Как пользоваться:\n"
        "1) Пришлите фото продуктов.\n"
        "2) Или напишите: 'курица, рис, лук'.\n"
        "3) Включите ежедневную рассылку: /daily 09:00 on\n"
        "КБЖУ — ориентировочные значения."
    )

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = storage.list_ingredients(update.effective_user.id)
    if not rows:
        return await update.message.reply_text("Ингредиентов нет. Пришлите фото или текст.")
    text = "Ваши ингредиенты:\n" + "\n".join(f"{i}. {n}" for i, n, _ in rows[:20])
    await update.message.reply_text(text)

async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage.clear_ingredients(update.effective_user.id)
    await update.message.reply_text("Список очищен ✅")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    time = None
    enabled = None
    if len(args) == 1:
        enabled = 1 if args[0].lower() == "on" else 0
    elif len(args) == 2:
        time = args[0]
        enabled = 1 if args[1].lower() == "on" else 0
    else:
        return await update.message.reply_text("Формат: /daily 09:00 on|off")

    if time:
        storage.upsert_user(update.effective_user.id, daily_time=time)
    if enabled is not None:
        storage.upsert_user(update.effective_user.id, enabled=enabled)
    await update.message.reply_text("Ежедневная рассылка включена ✅" if enabled else "Рассылка выключена 🛑")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    items = [x.strip() for x in text.split(",") if x.strip()]
    if not items:
        return await update.message.reply_text("Напиши продукты через запятую, например: курица, лук, морковь")

    # Показываем статус "печатает"
    try:
        await update.message.chat.send_action(action="typing")
    except Exception:
        pass

    # Вызываем Яндекс-провайдер (используем глобальный объект recipes)
    try:
        reply = await recipes.recipe_with_macros(items)
    except Exception as e:
        # Если ошибка — вернём понятный текст и лог
        await update.message.reply_text("Ошибка при обращении к AI: " + str(e))
        return

    # Сохраняем ингредиенты в хранилище
    try:
        storage.add_ingredients(update.effective_user.id, items)
    except Exception:
        # если storage ломается — не фейлим весь процесс
        pass

    # Telegram ограничение на сообщение ~4096 символов — разбиваем на части
    max_len = 4000
    for i in range(0, len(reply), max_len):
        await update.message.reply_text(reply[i:i + max_len])


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "how_photo":
        await q.message.reply_text("Нажмите скрепку → Фото/Видео → выберите фото (не как файл). Отправьте.")
    elif data == "daily_on":
        storage.upsert_user(q.from_user.id, enabled=1)
        await q.message.reply_text("Ежедневная рассылка включена ✅ (время см. /daily)")
    elif data == "daily_off":
        storage.upsert_user(q.from_user.id, enabled=0)
        await q.message.reply_text("Рассылка выключена 🛑")
    elif data == "list":
        fake_update = Update(update.update_id, message=q.message)
        await list_cmd(fake_update, context)