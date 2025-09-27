from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Удиви меня! (Рецепт дня)", callback_data="surprise_recipe")],
        [InlineKeyboardButton("🎯 Получить рецепт под мою цель", callback_data="goal_recipe")],
    ])

def goal_submenu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Загрузить фото продуктов", callback_data="upload_photo")],
        [InlineKeyboardButton("⌨️ Ввести продукты вручную", callback_data="manual_input")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ])

def premium_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Купить PRO", callback_data="buy_pro")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ])

def profile_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Изменить цель", callback_data="change_goal")],
        [InlineKeyboardButton("🍳 Мои продукты", callback_data="my_products")],
        [InlineKeyboardButton("🗑 Очистить продукты", callback_data="clear_products")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ])


def after_recipe_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔁 Сгенерировать другой", callback_data="regenerate")],
        [InlineKeyboardButton("💾 Сохранить рецепт", callback_data="save_recipe")],
        [InlineKeyboardButton("🔙 В меню", callback_data="back_to_main")]
    ])

# NEW: меню выбора цели
def goal_choice_menu():
    return InlineKeyboardMarkup([
        [# Первый ряд
        InlineKeyboardButton("💪 Похудеть", callback_data="goal:lose"),
        InlineKeyboardButton("🥑 ПП", callback_data="goal:pp")],

        [# Первый ряд
        InlineKeyboardButton("⏱ Быстро", callback_data="goal:fast"),
        InlineKeyboardButton("🍲 Обычные", callback_data="goal:normal")],

        [# Первый ряд
        InlineKeyboardButton("🥦 Веган", callback_data="goal:vegan"),
        InlineKeyboardButton("🥚 Кето-питание", callback_data="goal:keto")],
        
        # Первый ряд
        [InlineKeyboardButton("➕ Добавить продукты", callback_data="add_more")],
    ])