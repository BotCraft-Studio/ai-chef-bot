from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.keyboards import main_menu, goal_submenu, premium_menu, profile_menu
from app import storage
from app.providers.yandex_vision import YandexRecipes
recipes = YandexRecipes()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    storage.upsert_user(update.effective_user.id)
    await update.message.reply_text(
        "Привет! Я ваш личный повар 👨‍🍳\n\n"
        "Выберите опцию:",
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
    text = update.message.text
    
    # Если это ответ на запрос ручного ввода
    if not text.startswith('/'):  # не команда
        items = [x.strip() for x in text.split(",") if x.strip()]
        if items:
            from app.providers.yandex_vision import YandexRecipes
            ai = YandexRecipes()
            reply = await ai.recipe_with_macros(items)
            storage.add_ingredients(update.effective_user.id, items)
            await update.message.reply_text(reply, reply_markup=main_menu())
            return
    
    await update.message.reply_text("Напишите ингредиенты через запятую или используйте меню")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    
    if data == "surprise_recipe":
        # Рецепт дня из сезонных рецептов
        import datetime
        from app import seasonal
        from app.providers.yandex_vision import YandexRecipes
        
        month = datetime.datetime.now().month
        seasonal_recipes = seasonal.SEASONAL.get(month, [])
        recipe_name = seasonal_recipes[0] if seasonal_recipes else "Сезонный рецепт"
        
        ai = YandexRecipes()
        reply = await ai.recipe_with_macros([recipe_name])
        await q.message.edit_text(f"✨ Рецепт дня!\n\n{reply}", reply_markup=main_menu())
        
    elif data == "goal_recipe":
        # Подменю выбора способа ввода
        await q.message.edit_text(
            "🎯 Выберите способ ввода продуктов:",
            reply_markup=goal_submenu()
        )

    elif data == "buy_pro":
        await q.message.edit_text(
            "💳 <b>Оформление PRO подписки</b>\n\n"
            "Premium PRO на 12 месяцев:\n"
            "• Цена: 999 руб.\n"
            "• Доступ ко всем функциям\n"
            "• Техническая поддержка 24/7\n\n"
            "Для оплаты свяжитесь с @администратор",
            reply_markup=premium_menu(),
            parse_mode='HTML'
        )

    elif data == "change_goal":
        await q.message.edit_text(
            "🎯 <b>Изменить цель питания</b>\n\n"
            "Выберите вашу основную цель:\n"
            "• Похудение 🏃‍♂️\n"
            "• Поддержание веса ⚖️\n"
            "• Набор массы 💪\n"
            "• Здоровое питание 🥗\n\n"
            "Функция в разработке...",
            reply_markup=profile_menu(),
            parse_mode='HTML'
        )
        
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
        await q.message.edit_text(
            "Выберите опцию:",
            reply_markup=main_menu()
        )
        
    elif data == "upload_photo":
        await q.message.edit_text(
            "📷 Отправьте фото продуктов\n\n"
            "Совет: сфотографируйте продукты на светлом фоне для лучшего распознавания"
        )
        
    elif data == "manual_input":
        await q.message.edit_text(
            "⌨️ Введите продукты через запятую:\n\n"
            "Пример: курица, рис, лук, морковь\n\n"
            "Я предложу рецепт с расчетом КБЖУ!"
        )
        
    elif data == "back_to_main":
        await q.message.edit_text(
            "Выберите опцию:",
            reply_markup=main_menu()
        )
        
    elif data == "list":
        fake_update = Update(update.update_id, message=q.message)
        await list_cmd(fake_update, context)


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
 await update.message.reply_text(
    "🔄 Фото получено! Функция распознавания продуктов временно недоступна.\n\n"
    "Пожалуйста, введите продукты текстом через запятую.",
    reply_markup=main_menu()  # ← ИСПРАВЛЕНО: = вместо -
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
    
    await update.message.reply_text(
        f"👤 <b>Ваш профиль</b>\n\n"
        f"📊 Статистика:\n"
        f"• Сохранено продуктов: {ingredients_count}\n"
        f"• Последние добавления: {', '.join([name for _, name, _ in ingredients[:3]]) if ingredients else 'нет'}\n\n"
        f"Выберите действие:",
        reply_markup=profile_menu(),
        parse_mode='HTML'
    )