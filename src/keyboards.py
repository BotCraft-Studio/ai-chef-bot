from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from utils.query_utils import (
    ADD_INGREDIENT,
    BUY_PRO,
    CHANGE_GOAL,
    CLEAR_INGREDIENTS,
    DAILY_RECIPE,
    GOAL_FAST,
    GOAL_KETO,
    GOAL_LOSE,
    GOAL_NORMAL,
    GOAL_PP,
    GOAL_RECIPE,
    GOAL_VEGAN,
    MAIN_MENU,
    MANUAL_INPUT,
    MY_INGREDIENTS,
    REGENERATE_RECIPE,
    SAVE_RECIPE,
    UPLOAD_PHOTO
)


def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Удиви меня! (Рецепт дня)", callback_data=DAILY_RECIPE)],
        [InlineKeyboardButton("🎯 Получить рецепт под мою цель", callback_data=GOAL_RECIPE)],
    ])


def goal_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Загрузить фото продуктов", callback_data=UPLOAD_PHOTO)],
        [InlineKeyboardButton("⌨️ Ввести продукты вручную", callback_data=MANUAL_INPUT)],
        [InlineKeyboardButton("🔙 Назад", callback_data=MAIN_MENU)],
    ])


def premium_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Купить PRO", callback_data=BUY_PRO)],
        [InlineKeyboardButton("🔙 Назад", callback_data=MAIN_MENU)],
    ])


def profile_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Изменить цель", callback_data=CHANGE_GOAL)],
        [InlineKeyboardButton("🍳 Мои продукты", callback_data=MY_INGREDIENTS)],
        [InlineKeyboardButton("🗑 Очистить продукты", callback_data=CLEAR_INGREDIENTS)],
        [InlineKeyboardButton("🔙 Назад", callback_data=MAIN_MENU)],
    ])


def after_recipe_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Сгенерировать другой", callback_data=REGENERATE_RECIPE)],
        [InlineKeyboardButton("💾 Сохранить рецепт", callback_data=SAVE_RECIPE)],
        [InlineKeyboardButton("🔙 В меню", callback_data=MAIN_MENU)],
    ])


# NEW: меню выбора цели
def goal_choice_menu():
    return InlineKeyboardMarkup([
        [  # Первый ряд
            InlineKeyboardButton("💪 Похудеть", callback_data=GOAL_LOSE),
            InlineKeyboardButton("🥑 ПП", callback_data=GOAL_PP)],

        [  # Первый ряд
            InlineKeyboardButton("⏱ Быстро", callback_data=GOAL_FAST),
            InlineKeyboardButton("🍲 Обычные", callback_data=GOAL_NORMAL)],

        [  # Первый ряд
            InlineKeyboardButton("🥦 Веган", callback_data=GOAL_VEGAN),
            InlineKeyboardButton("🥚 Кето-питание", callback_data=GOAL_KETO)],

        # Первый ряд
        [InlineKeyboardButton("➕ Добавить продукты", callback_data=ADD_INGREDIENT)],
    ])

def photoback_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Загрузить фото продуктов", callback_data=UPLOAD_PHOTO)],
        [InlineKeyboardButton("🔙 Назад", callback_data=GOAL_RECIPE)],
    ])

def textback_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⌨️ Ввести продукты вручную", callback_data=MANUAL_INPUT)],
        [InlineKeyboardButton("🔙 Назад", callback_data=GOAL_RECIPE)],
    ])
