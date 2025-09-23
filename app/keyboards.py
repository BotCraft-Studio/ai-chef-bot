from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Как отправить фото", callback_data="how_photo")],
        [InlineKeyboardButton("📬 Ежедневная подборка", callback_data="daily_on")],
        [InlineKeyboardButton("🛑 Выключить рассылку", callback_data="daily_off")],
        [InlineKeyboardButton("📋 Мои ингредиенты", callback_data="list")],
    ])
