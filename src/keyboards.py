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
    UPLOAD_PHOTO,
    BACK_TO_GOAL_SELECTION,
    MY_RECIPES,
    SHARE_RECIPE,
    CHANGE_PRODUCTS
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


def after_recipe_menu(share_url=None):
    first_row = [
        InlineKeyboardButton("🔁 Другой вариант", callback_data=REGENERATE_RECIPE),
        InlineKeyboardButton("❤️ В избранное", callback_data=SAVE_RECIPE)
    ]
    second_row = [
        InlineKeyboardButton("📖 Мои рецепты", callback_data=MY_RECIPES),
        InlineKeyboardButton("📤 Поделиться", url=share_url) if share_url else None,
    ] if share_url is not None else [
        InlineKeyboardButton("📖 Мои рецепты", callback_data=MY_RECIPES)
    ]
    third_row = [
        InlineKeyboardButton("🍎 Новый список продуктов", callback_data=CHANGE_PRODUCTS),
    ]

    return InlineKeyboardMarkup([
        first_row,second_row,third_row
    ])


# NEW: меню выбора цели
def goal_choice_menu():
    return InlineKeyboardMarkup([
        [  # Первый ряд
            InlineKeyboardButton("💪 Похудеть", callback_data=GOAL_LOSE),
            InlineKeyboardButton("🥑 ПП", callback_data=GOAL_PP)],

        [  # Второй ряд
            InlineKeyboardButton("⏱ Быстро", callback_data=GOAL_FAST),
            InlineKeyboardButton("🍲 Обычные", callback_data=GOAL_NORMAL)],

        [  # Третий ряд
            InlineKeyboardButton("🥦 Веган", callback_data=GOAL_VEGAN),
            InlineKeyboardButton("🥚 Кето-питание", callback_data=GOAL_KETO)],

        # Четвертый ряд
        [InlineKeyboardButton("➕ Добавить продукты", callback_data=ADD_INGREDIENT)],
    ])


def photoback_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Загрузить фото продуктов", callback_data=UPLOAD_PHOTO)],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_recipe")],
    ])


def textback_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⌨️ Ввести продукты вручную", callback_data=MANUAL_INPUT)],
        [InlineKeyboardButton("🔙 Назад", callback_data=GOAL_RECIPE)],
    ])


def time_selection_menu():
    """Клавиатура для выбора времени готовки (2 кнопки в ряд)"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from utils.bot_utils import TIME_OPTIONS

    # Создаем список пар кнопок (по 2 в каждом ряду)
    buttons = []
    time_items = list(TIME_OPTIONS.items())

    # Первый ряд: первые 2 кнопки
    buttons.append([
        InlineKeyboardButton(time_items[0][1], callback_data=time_items[0][0]),  # До 15 мин
        InlineKeyboardButton(time_items[1][1], callback_data=time_items[1][0])  # До 30 мин
    ])

    # Второй ряд: следующие 2 кнопки
    buttons.append([
        InlineKeyboardButton(time_items[2][1], callback_data=time_items[2][0]),  # До 60 мин
        InlineKeyboardButton(time_items[3][1], callback_data=time_items[3][0])  # Не важно
    ])

    # Третий ряд: кнопка "Назад" (одна на весь ряд)
    buttons.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_goal_selection")])

    return InlineKeyboardMarkup(buttons)
