from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.constants import ParseMode  # NEW
import re  # NEW
import html  # NEW
from app.keyboards import main_menu, goal_submenu, premium_menu, profile_menu, after_recipe_menu, goal_choice_menu
from app import storage
from app.providers.yandex_vision import YandexRecipes

recipes = YandexRecipes()

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# NEW: аккуратно превращаем markdown-звёздочки в HTML для Телеграма
def format_recipe_for_telegram(ai_text: str) -> str:
    """
    Делает текст из Яндекс GPT аккуратным для Телеграма:
    - **Заголовок** -> <b>Заголовок</b>
    - Строки вида "* Пункт" -> "• Пункт"
    - Экранирует HTML-символы, чтобы текст не ломал разметку
    """
    # 1) экранируем любые <, >, & и т.п.
    text = html.escape(ai_text)

    # 2) **Жирный** -> <b>Жирный</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # 3) В начале строк "* " -> "• "
    text = re.sub(r'(?m)^[ \t]*\* +', '• ', text)

    # 4) приводим множественные пустые строки к двум
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    return text




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
в
🎯 Советы:
• Используйте 📸 фото для быстрого ввода
• Указывайте 🎯 цель для персонализированных рецептов
• Сохраняйте 🍳 любимые рецепты в профиле
    """
    await update.message.reply_text(text)

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = storage.list_ingredients(update.effective_user.id)
    if not rows:
        return await update.message.reply_text(
            "📦 Ингредиентов нет.\n\n"
            "✨ Добавьте продукты через меню!"
        )
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
    text = update.message.text.strip() if update.message and update.message.text else ""
    user_id = update.effective_user.id

    # Если бот занят — предупреждаем
    if storage.get_flag(user_id, "busy"):
        return await update.message.reply_text("⏳ Я сейчас генерирую рецепт — подожди чуть-чуть, пожалуйста.")

    # Принимаем текст ТОЛЬКО если пользователь в режиме ручного ввода
    if storage.get_flag(user_id, "await_manual"):
        items = [x.strip() for x in text.split(",") if x.strip()]
        if not items:
            return await update.message.reply_text(
                "Похоже, список пуст. Введите продукты через запятую, например: курица, рис, лук"
            )

        # Сохраняем товары пользователя
        storage.add_ingredients(user_id, items)

        # Выключаем режим ручного ввода — дальше ждём выбор цели
        storage.set_flag(user_id, "await_manual", False)

        # Список для показа
        products_list = "\n".join(f"• {name}" for _, name, _ in storage.list_ingredients(user_id))
        reply_text = (
            "Вот твои продукты:\n"
            f"{products_list}\n\n"
            "Самое важное — под какую цель делаем рецепт?"
        )

        return await update.message.reply_text(reply_text, reply_markup=goal_choice_menu())

    # Иначе — подсказка
    keyboard = [
        [InlineKeyboardButton("⌨️ Ввести продукты вручную", callback_data="manual_input")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Чтобы ввести продукты вручную, нажмите кнопку ниже:",
        reply_markup=reply_markup
    )

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
        pretty = format_recipe_for_telegram(reply)  # NEW
        await q.message.edit_text(
            f"✨ Рецепт дня!\n\n{pretty}",
            reply_markup=main_menu(),
            parse_mode=ParseMode.HTML,              # NEW
            disable_web_page_preview=True           # NEW
        )

    elif data == "add_more":
        # Включаем режим ручного ввода, чтобы принять доп. продукты
        storage.set_flag(user_id, "await_manual", True)
        await q.message.edit_text(
            "Добавь продукты через запятую, я их ДОБАВЛЮ к текущему списку.\n\n"
            "Например: сыр, помидоры, оливковое масло"
        )

    elif data.startswith("goal:"):
        goal_map = {
            "goal:lose":   "похудение",
            "goal:pp":     "правильное питание (ПП)",
            "goal:fast":   "быстрый рецепт",
            "goal:normal": "обычный рецепт",
            "goal:vegan":  "веганский рецепт",
            "goal:keto":   "кето-рецепт",
        }
        goal_name = goal_map.get(data, "обычный рецепт")

        # Берём актуальные продукты из хранилища
        rows = storage.list_ingredients(user_id)
        items = [name for _, name, _ in rows]

        if not items:
            return await q.message.edit_text(
                "Не вижу продуктов. Введите продукты через запятую, например: курица, рис, лук",
                reply_markup=main_menu()
            )

        # Генерируем рецепт
        if storage.get_flag(user_id, "busy"):
            return await q.message.reply_text("⏳ Я уже генерирую рецепт — подождите немного.")
        storage.set_flag(user_id, "busy", True)

        try:
            ai = YandexRecipes()
            # Простой способ «передать» цель модели — добавить строку-установку
            prompt_items = [f"Цель: {goal_name}"] + items
            reply = await ai.recipe_with_macros(prompt_items)
            pretty = format_recipe_for_telegram(reply)

            # сохраним последний рецепт
            context.user_data["last_generated_recipe"] = {
                "text": reply,
                "ingredients": items,
                "title": items[0] if items else "Рецепт"
            }
        except Exception as e:
            storage.set_flag(user_id, "busy", False)
            return await q.message.edit_text(f"Ошибка при запросе рецепта: {e}")

        storage.set_flag(user_id, "busy", False)

        await q.message.edit_text(
            pretty,
            reply_markup=after_recipe_menu(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )    

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
            pretty = format_recipe_for_telegram(reply)
        except Exception as e:
            storage.set_flag(user_id, "busy", False)
            return await q.message.edit_text(f"Ошибка генерации: {e}", reply_markup=main_menu())
        storage.set_flag(user_id, "busy", False)
        context.user_data["last_generated_recipe"] = {"text": reply, "ingredients": last, "title": last[0] if last else "Рецепт"}
        await q.message.edit_text(
            pretty,
            reply_markup=after_recipe_menu(),
            parse_mode=ParseMode.HTML,              # NEW
            disable_web_page_preview=True           # NEW
        )

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