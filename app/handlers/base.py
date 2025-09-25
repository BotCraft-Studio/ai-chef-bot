from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.keyboards import main_menu, goal_submenu, premium_menu, profile_menu, after_recipe_menu
from app import storage
from app.providers.yandex_vision import YandexRecipes

recipes = YandexRecipes()

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🍳 Добро пожаловать в AI-Chef! 👨‍🍳

Я ваш персональный шеф-повар с искусственным интеллектом! 

✨ Что я умею:

• Создавать рецепты из ваших продуктов
• Рассчитывать точное КБЖУ для каждой порции
• Предлагать сезонные рецепты дня
• Помогать достигать ваших целей питания

👇 Выберите действие:
    """
    await update.message.reply_text(text, reply_markup=main_menu())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
ℹ️ Как пользоваться AI-Chef 🍳

✨ 3 простых шага:
1. 📸 Сфотографируйте продукты или 📝 напишите список через запятую
2. 🍳 Получите рецепт с точным расчетом КБЖУ
3. ⭐️ Сохраняйте понравившиеся рецепты в профиле

🕒 Ежедневные рецепты:
 /daily 09:00 on` — получайте рецепт в 9 утра
 /daily off` — отключить рассылку

📊 О расчетах КБЖУ:
• Значения ориентировочные, для стандартных порций
• Точность зависит от правильности ввода продуктов
• Для точных расчетов укажите вес продуктов

🎯 Советы:
• Используйте 📸 фото для быстрого ввода
• Указывайте 🎯 цель для персонализированных рецептов
• Сохраняйте 🍳 любимые рецепты в профиле
    """
    await update.message.reply_text(text)

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = storage.list_ingredients(update.effective_user.id)
    if not rows:
        return await update.message.reply_text("Ингредиентов нет. Пришлите фото или текст.")
    text = "Ваши ингредиенты:\n" + "\n".join(f"{i}. {n}" for i, n, _ in rows[:50])
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
    text = update.message.text.strip() if update.message and update.message.text else ""
    user_id = update.effective_user.id

    # Если бот занят — предупреждаем
    if storage.get_flag(user_id, "busy"):
        return await update.message.reply_text("⏳ Я сейчас генерирую рецепт — подожди чуть-чуть, пожалуйста.")

    # Принимаем текст ТОЛЬКО если пользователь в режиме ручного ввода
    if storage.get_flag(user_id, "await_manual"):
        items = [x.strip() for x in text.split(",") if x.strip()]
        if not items:
            return await update.message.reply_text("Похоже, список пуст. Введите продукты через запятую, например: курица, рис, лук")
        # выставляем флаг busy
        storage.set_flag(user_id, "busy", True)
        try:
            storage.add_ingredients(user_id, items)
            ai = YandexRecipes()
            reply = await ai.recipe_with_macros(items)
        except Exception as e:
            storage.set_flag(user_id, "busy", False)
            storage.set_flag(user_id, "await_manual", False)
            return await update.message.reply_text(f"Ошибка при запросе рецепта: {e}")
        # Сбросим флаги
        storage.set_flag(user_id, "busy", False)
        storage.set_flag(user_id, "await_manual", False)

        # Сохраняем последний сгенерированный рецепт в context.user_data
        context.user_data["last_generated_recipe"] = {
            "text": reply,
            "ingredients": items,
            "title": items[0] if items else "Рецепт"
        }

        await update.message.reply_text(reply, reply_markup=after_recipe_menu())
        return

    # Иначе — подсказка
    await update.message.reply_text("Чтобы ввести продукты вручную, нажмите: ⌨️ Ввести продукты вручную в меню.", reply_markup=main_menu())


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = q.from_user.id

    if data == "surprise_recipe":
        # (оставляем как есть — пример генерации по одному ингредиенту)
        import datetime
        from app import seasonal
        month = datetime.datetime.now().month
        seasonal_recipes = seasonal.SEASONAL.get(month, [])
        recipe_name = seasonal_recipes[0] if seasonal_recipes else "Сезонный рецепт"
        ai = YandexRecipes()
        reply = await ai.recipe_with_macros([recipe_name])
        await q.message.edit_text(f"✨ Рецепт дня!\n\n{reply}", reply_markup=main_menu())

    elif data == "goal_recipe":
        await q.message.edit_text("🎯 Выберите способ ввода продуктов:", reply_markup=goal_submenu())

    elif data == "upload_photo":
        await q.message.edit_text("📷 Отправьте фото продуктов\n\nСовет: сфотографируйте продукты на светлом фоне для лучшего распознавания")

    elif data == "manual_input":
        # Установим флаг ожидания ручного ввода
        storage.set_flag(user_id, "await_manual", True)
        await q.message.edit_text(
            "⌨️ Введите продукты через запятую:\n\n"
            "Пример: курица, рис, лук, морковь\n\n"
            "Я предложу рецепт с расчетом КБЖУ!",
        )

    elif data == "regenerate":
        last = storage.get_last_ingredients(user_id)
        if not last:
            return await q.message.edit_text("Нет последнего списка ингредиентов. Сначала введите продукты.", reply_markup=main_menu())
        if storage.get_flag(user_id, "busy"):
            return await q.message.reply_text("⏳ Я уже генерирую рецепт — подождите немного.")
        storage.set_flag(user_id, "busy", True)
        try:
            ai = YandexRecipes()
            reply = await ai.recipe_with_macros(last)
        except Exception as e:
            storage.set_flag(user_id, "busy", False)
            return await q.message.edit_text(f"Ошибка генерации: {e}", reply_markup=main_menu())
        storage.set_flag(user_id, "busy", False)
        context.user_data["last_generated_recipe"] = {"text": reply, "ingredients": last, "title": last[0] if last else "Рецепт"}
        await q.message.edit_text(reply, reply_markup=after_recipe_menu())

    elif data == "save_recipe":
        last = context.user_data.get("last_generated_recipe")
        if not last:
            return await q.message.reply_text("Нет рецепта для сохранения. Сначала получите рецепт.", reply_markup=main_menu())
        storage.save_recipe_for_user(user_id, last.get("title", "Рецепт"), last["text"], last["ingredients"])
        await q.message.reply_text("✅ Рецепт сохранён в вашем списке.", reply_markup=profile_menu())

    elif data == "my_products":
        ingredients = storage.list_ingredients(q.from_user.id)
        if not ingredients:
            text = "🍳 <b>Ваши продукты</b>\n\nСписок пуст. Добавьте продукты через меню."
        else:
            text = "🍳 <b>Ваши продукты</b>\n\n" + "\n".join([f"• {name}" for _, name, _ in ingredients[:10]])
            if len(ingredients) > 10:
                text += f"\n\n... и еще {len(ingredients) - 10} продуктов"
        await q.message.edit_text(text, reply_markup=profile_menu(), parse_mode='HTML')

    elif data == "clear_products":
        storage.clear_ingredients(q.from_user.id)
        await q.message.edit_text(
            "🗑 <b>Список продуктов очищен</b>\n\n"
            "Все ваши продукты удалены. Можете начать заново!",
            reply_markup=profile_menu(),
            parse_mode='HTML'
        )

    elif data == "back_to_main":
        await q.message.edit_text("Выберите опцию:", reply_markup=main_menu())

    elif data == "buy_pro":
        await q.message.edit_text(
            "💳 <b>Оформление PRO подписки</b>\n\n"
            "Для оплаты свяжитесь с @администратор",
            reply_markup=premium_menu(),
            parse_mode='HTML'
        )

    elif data == "change_goal":
        await q.message.edit_text("🎯 <b>Изменить цель питания</b>\n\nФункция в разработке...", reply_markup=profile_menu(), parse_mode='HTML')


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # если распознавание пока недоступно — подсказка
    await update.message.reply_text(
        "🔄 Фото получено! Функция распознавания продуктов временно недоступна.\n\n"
        "Пожалуйста, введите продукты текстом через запятую.",
        reply_markup=main_menu()
    )
 
async def premium_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
     await update.message.reply_text(
        "🌟 <b>Premium рецепты PRO</b>\n\n"
        "Получите доступ к эксклюзивным функциям:\n"
        "• Более 1000 премиум рецептов\n"
        "• Персональный план питания\n"
        "• Расширенная база продуктов\n"
        "• Приоритетная поддержка\n\n"
        "Выберите действие:",
        reply_markup=premium_menu(),
        parse_mode='HTML'
    )
     
async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ingredients = storage.list_ingredients(user_id)
    ingredients_count = len(ingredients)
    last_three = ', '.join([name for _, name, _ in ingredients[:3]]) if ingredients else 'нет'
    await update.message.reply_text(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"📊 Статистика:\n"
        f"• Сохранено продуктов: {ingredients_count}\n"
        f"• Последние добавления: {last_three}\n\n"
        f"Выберите действие:",
        reply_markup=profile_menu(),
        parse_mode='HTML'
    )