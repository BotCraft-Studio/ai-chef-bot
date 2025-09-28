"""
Модуль отвечает за обработку команд, поступающих от пользователя
"""

from telegram import Update
from telegram.ext import ContextTypes

import storage
from keyboards import premium_menu, profile_menu, main_menu


async def start_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE):
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


async def help_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE):
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


async def list_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    rows = storage.list_ingredients(update.effective_user.id)
    if not rows:
        return await update.message.reply_text(
            "📦 Ингредиентов нет.\n\n"
            "✨ Добавьте продукты через меню!"
        )
    text = "Ваши ингредиенты:\n" + "\n".join(f"{i}. {n}" for i, n, _ in rows[:20])
    await update.message.reply_text(text)

    return None


async def del_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE):
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

    return None


async def premium_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE):
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


async def profile_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE):
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
