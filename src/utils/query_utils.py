"""
Переменные для определения запроса пользователя исходя из полученного сообщения
"""

ADD_INGREDIENT = "add_ingredient"       # Добавить ингредиент (при ручном вводе)
BUY_PRO = "buy_pro"                     # Купить платную подписку
MY_RECIPES = "profile_my_recipes"       # Мои сохраненные рецепты
MY_SUBSCRIBE = "profile_subscribe"      # Управление подпиской
DAILY_RECIPE = "daily_recipe"           # Рецепт дня
BACK_TO_PROFILE = "back_to_profile"     # Назад к профилю
GOAL_FAST = "goal_fast"                 # Цель - Быстрый рецепт
GOAL_KETO = "goal_keto"                 # Цель - Кето рецепт
GOAL_LOSE = "goal_lose"                 # Цель - Похудение
GOAL_NORMAL = "goal_normal"             # Цель - Обычный рецепт
GOAL_PP = "goal_pp"                     # Цель - ПП
GOAL_RECIPE = "goal_recipe"             # Выбрать цель, под которую нужен рецепт
GOAL_VEGAN = "goal_vegan"               # Цель - Веганский рецепт
MAIN_MENU = "main_menu"                 # Вернуться в главное меню
MANUAL_INPUT = "manual_input"           # Ручной ввод ингредиентов
REGENERATE_RECIPE = "regenerate_recipe" # Сгенерировать полученный рецепт еще раз
SAVE_RECIPE = "save_recipe"             # Сохранить рецепт
UPLOAD_PHOTO = "upload_photo"           # Загрузить фото/картинку с ингредиентами
BACK_TO_GOAL_SELECTION = "back_to_goal_selection"
SHARE_RECIPE = "share_recipe"           # Поделиться рецептом
CHANGE_PRODUCTS = "change_products"     # Изменить продукты

# Хэлпер smart_capitalize (для красивого списка)
def smart_capitalize(s: str) -> str:
    s = s.strip()
    return s[:1].upper() + s[1:] if s else s
