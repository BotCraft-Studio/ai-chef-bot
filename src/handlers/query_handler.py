"""
Модуль отвечает за обработку запросов, поступающих от пользователя
"""

import datetime
import html
import logging
import re

from telegram import Update, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from telegram._utils.defaultvalue import DEFAULT_TRUE
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import storage

from utils.query_utils import smart_capitalize
from keyboards import main_menu, goal_submenu, after_recipe_menu, profile_menu, premium_menu, textback_submenu, photoback_submenu, time_selection_menu, goal_choice_menu
from providers.gigachat import GigaChatText
from utils.bot_utils import APPEND_MODE, SESSION_ITEMS, AWAIT_MANUAL, BUSY, GOAL_CODE, LAST_GENERATED_RECIPE, SELECTED_TIME, TIME_OPTIONS
from utils.goal_utils import GOALS
from utils.query_utils import MY_RECIPES, SHARE_RECIPE, CHANGE_PRODUCTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

AI = GigaChatText()

SEASONAL = {
    1: ["Тыквенный крем-суп", "Запечённые корнеплоды", "Глинтвейн без алкоголя"],
    2: ["Луковый суп", "Паста с грибами", "Чечевичный дал"],
    3: ["Салат с редисом и яйцом", "Крем-суп из шпината", "Окрошка без кваса"],
    4: ["Ризотто со спаржей", "Курица с горошком", "Клубничный смузи"],
    5: ["Салат нисуаз", "Шашлык из овощей", "Табуле"],
    6: ["Окрошка/холодник", "Поке с лососем", "Тарт со спаржей"],
    7: ["Гаспачо", "Паста с томатами", "Кобб-салат"],
    8: ["Салат с арбузом и фетой", "Рататуй", "Кукурузные оладьи"],
    9: ["Тыква с фетой", "Шарлотка", "Лёгкий борщ"],
    10: ["Жаркое с грибами", "Перлотто с тыквой", "Пирог с грушей"],
    11: ["Щи из квашеной капусты", "Плов с айвой", "Крем-суп из брокколи"],
    12: ["Утка с яблоками", "Сырный крем-суп", "Имбирное печенье"],
}

async def daily_recipe(query: CallbackQuery | None):
    # 1) Показываем баннер перед генерацией (редактируем ТО ЖЕ сообщение → будет красивая анимация)
    await query.message.edit_text(
        ai_progress_text(subtitle="Рецепт дня на основе сезонных продуктов"),
        parse_mode=ParseMode.HTML
    )

    # 2) Выбираем тему для рецепта дня (как и было)
    month = datetime.datetime.now().month
    seasonal_recipes = SEASONAL.get(month, [])
    recipe_name = seasonal_recipes[0] if seasonal_recipes else "Сезонный рецепт"

    try:
        # 3) Генерируем рецепт у ИИ
        reply = await AI.parse_ingredients([recipe_name])
        pretty = format_recipe_for_telegram(reply)

        # 4) Заменяем баннер на готовый рецепт (снова редактируем то же сообщение → вторая анимация)
        await query.message.edit_text(
            f"✨ Рецепт дня!\n\n{pretty}",
            reply_markup=after_recipe_menu(share_url=None),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception:
        # лаконичное сообщение об ошибке (тоже редактирование, без спама новыми сообщениями)
        await query.message.edit_text(
            "⚠️ Не удалось сгенерировать рецепт дня. Попробуйте ещё раз чуть позже.",
            parse_mode=ParseMode.HTML
        )


async def add_ingredient(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault(SESSION_ITEMS, [])
    context.user_data[APPEND_MODE] = True
    context.user_data[AWAIT_MANUAL] = True

    # Тоже reply_text — пречек остаётся видимым
    await query.message.reply_text(
        "Добавь продукты через запятую, я их ДОБАВЛЮ к текущему списку.\n\n"
        "Например: сыр, помидоры, оливковое масло"
    )


async def goal_recipe(query: CallbackQuery | None):
    await query.message.edit_text("🎯 Выберите способ ввода продуктов:", reply_markup=goal_submenu())


async def upload_photo(query: CallbackQuery | None):
    await query.message.edit_text(
        "📷 Отправьте фото продуктов\n\nСовет: сфотографируйте продукты на светлом фоне для лучшего распознавания",
        reply_markup=textback_submenu(),
    )


async def manual_input(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    # чистый лист в СЕССИИ
    context.user_data[SESSION_ITEMS] = []
    context.user_data[APPEND_MODE] = False
    context.user_data[AWAIT_MANUAL] = True

    # ВАЖНО: не edit_text (это замещает пречек), а reply_text — пречек останется!
    await query.message.edit_text(
        "⌨️ Введите продукты через запятую:\n\nПример: курица, рис, лук, морковь",
        reply_markup=photoback_submenu(),
    )


async def goal_recipe_choice(user_input: str, query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    # 1) продукты берём из того, что пользователь только что ввёл
    items = context.user_data.get(SESSION_ITEMS, [])
    if not items:
        return await query.message.reply_text("Сначала введите продукты через запятую.")

    # 2) читаем «человеческое» название цели
    goal_name = GOALS.get(user_input, "Обычный домашний рецепт")

    # 3) проверка занятости
    if bool(context.user_data.get(BUSY)):
        return await query.message.reply_text("⏳ Я уже генерирую рецепт — подождите немного.")
    context.user_data[BUSY] = True  # не забудь: и читаем, и пишем один и тот же ключ

    try:
        # (а) показываем баннер — это даст красивую анимацию «рассыпания»
        await query.message.edit_text(
            ai_progress_text(subtitle=f"Цель: <i>{goal_name}</i>"),
            parse_mode=ParseMode.HTML
        )

        # (б) вызываем ИИ (как и раньше)
        items_with_goal = [f"Цель: {goal_name}"] + items
        reply = await AI.parse_ingredients(items_with_goal)

        # (в) приводим текст к красивому HTML (как у тебя уже сделано)
        pretty = format_recipe_for_telegram(reply)

        # (г) сохраняем для кнопки «Сгенерировать другой»
        context.user_data[GOAL_CODE] = user_input  # например, "goal_pp"
        context.user_data[LAST_GENERATED_RECIPE] = {
            "text": reply,
            "ingredients": items,
            "title": items[0] if items else "Рецепт"
        }

        # (д) заменяем баннер на готовый рецепт (ещё одна красивая анимация)
        await query.message.edit_text(
            pretty,
            reply_markup=after_recipe_menu(share_url=None),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(e)
        await query.message.edit_text("⚠️ Возникла ошибка при запросе генерации рецепта.")
    finally:
        context.user_data[BUSY] = False

    return None

async def regenerate_recipe(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует новый рецепт с сильным запросом на разнообразие"""
    last_recipe_data = context.user_data.get(LAST_GENERATED_RECIPE)

    if not last_recipe_data:
        return await query.message.edit_text(
            "Нет последнего списка ингредиентов. Сначала введите продукты.",
            reply_markup=main_menu()
        )

    if context.user_data.get(BUSY):
        return await query.message.reply_text("⏳ Я уже генерирую рецепт — подождите немного.")

    context.user_data[BUSY] = True

    try:
        await query.message.edit_text(
            ai_progress_text(subtitle="Создаю совершенно новый вариант"),
            parse_mode=ParseMode.HTML
        )

        ingredients = last_recipe_data.get("ingredients", [])
        goal_code = context.user_data.get(GOAL_CODE, "goal_normal")
        time_code = context.user_data.get(SELECTED_TIME, "time_any")

        goal_name = GOALS.get(goal_code, "Обычный домашний рецепт")
        time_display = TIME_OPTIONS.get(time_code, "Не важно")

        # Сильный запрос на разнообразие
        items_with_variation = [
            f"Цель: {goal_name}",
            f"Время готовки: {time_display}",
            "ВАЖНО: Создай совершенно другой рецепт, не похожий на предыдущий",
            "Используй другой тип блюда (если был суп - сделай второе, и наоборот)",
            "Примени другие техники приготовления",
            "Измени основные сочетания ингредиентов",
            "Предложи альтернативную кухню или стиль",
            "Сделай рецепт максимально отличным от обычного подхода"
        ] + ingredients

        reply = await AI.parse_ingredients(items_with_variation)
        pretty = format_recipe_for_telegram(reply)

        # Обновляем последний рецепт
        context.user_data[LAST_GENERATED_RECIPE] = {
            "text": reply,
            "ingredients": ingredients,
            "title": ingredients[0] if ingredients else "Рецепт"
        }

        # Создаем ссылку для шаринга
        recipe_preview = reply[:2000] + "..." if len(reply) > 2000 else reply
        share_text = f"🍳 {ingredients[0] if ingredients else 'Рецепт'}\n\n{recipe_preview}\n\n✨ Рецепт от @Cook_Br1o_bot"
        import urllib.parse
        encoded_text = urllib.parse.quote(share_text)
        share_url = f"https://t.me/share/url?url=https://t.me/Cook_Br1o_bot&text={encoded_text}"

        await query.message.edit_text(
            pretty,
            reply_markup=after_recipe_menu(share_url=share_url),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Ошибка при регенерации рецепта: {e}")
        await query.message.edit_text(
            "⚠️ Не удалось сгенерировать новый рецепт. Попробуйте позже.",
            reply_markup=after_recipe_menu(share_url=None)
        )
    finally:
        context.user_data[BUSY] = False

    return None


async def save_recipe(user_id: int, query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    last_generated_recipe = context.user_data.get(LAST_GENERATED_RECIPE)

    if not last_generated_recipe:
        return await query.message.reply_text(
            "Нет рецепта для сохранения. Сначала получите рецепт.",
            reply_markup=main_menu()
        )

    storage.save_recipe_for_user(user_id,
                                 last_generated_recipe.get("title", "Рецепт"),
                                 last_generated_recipe["text"],
                                 last_generated_recipe["ingredients"])
    await query.message.reply_text("✅ Рецепт сохранён в вашем списке.", reply_markup=after_recipe_menu(share_url=None))

    return None


async def my_ingredients(query: CallbackQuery | None):
    ingredients = storage.list_ingredients(query.from_user.id)

    if not ingredients:
        text = "🍳 <b>Ваши продукты</b>\n\nСписок пуст. Добавьте продукты через меню."
    else:
        text = "🍳 <b>Ваши продукты</b>\n\n" + "\n".join([f"• {name}" for _, name, _ in ingredients[:10]])
        if len(ingredients) > 10:
            text += f"\n\n... и еще {len(ingredients) - 10} продуктов"

    await query.message.edit_text(text, reply_markup=profile_menu(), parse_mode='HTML')


async def clear_ingredients(user_id: int, query: CallbackQuery | None):
    storage.clear_ingredients(user_id)
    await query.message.edit_text(
        "🗑 <b>Список продуктов очищен</b>\n\n"
        "Все ваши продукты удалены. Можете начать заново!",
        reply_markup=profile_menu(),
        parse_mode='HTML'
    )


async def back_to_main_menu(query: CallbackQuery | None):
    await query.message.edit_text("Выберите опцию:", reply_markup=main_menu())


async def buy_pro(query: CallbackQuery | None):
    await query.message.edit_text(
        "💳 <b>Оформление PRO подписки</b>\n\n"
        "Для оплата свяжитесь с @администратор",
        reply_markup=premium_menu(),
        parse_mode='HTML'
    )


async def change_goal(query: CallbackQuery | None):
    await query.message.edit_text(
        "🎯 <b>Изменить цель питания</b>\n\nФункция в разработке...",
        reply_markup=profile_menu(),
        parse_mode='HTML'
    )


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


# НОВОЕ: Информационное сообщение при генерации рецепта
def ai_progress_text(subtitle: str = "") -> str:
    subtitle = f"\n{subtitle}" if subtitle else ""
    return (
        "🤖 <b>Генерирую рецепт с помощью ИИ</b>"
        f"{subtitle}\n"
        "⏳ Пожалуйста, подождите 5–10 секунд…"
    )


async def show_time_selection_after_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню выбора времени после текстового ввода"""
    items = context.user_data.get(SESSION_ITEMS, [])

    if not items:
        return await update.message.reply_text(
            "Сначала введите продукты",
            reply_markup=main_menu()
        )

    # Красиво показываем продукты
    def smart_capitalize(s: str) -> str:
        return " ".join(w[:1].upper() + w[1:] for w in s.split())

    items_text = "\n".join([f"• {smart_capitalize(item)}" for item in items[:5]])
    if len(items) > 5:
        items_text += f"\n• ... и ещё {len(items) - 5} продуктов"

    # Используем reply_text вместо edit_text
    await update.message.reply_text(
        f"🍳 <b>Ваши продукты</b> ({len(items)} шт.):\n\n"
        f"{items_text}\n\n"
        f"⏰ <b>Выберите время готовки:</b>",
        reply_markup=time_selection_menu(),
        parse_mode=ParseMode.HTML
    )

async def goal_recipe_choice_with_time(goal_code: str, time_code: str, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует рецепт с учётом цели и времени"""
    items = context.user_data.get(SESSION_ITEMS, [])
    if not items:
        return await query.message.reply_text("Сначала введите продукты через запятую.")

    goal_name = GOALS.get(goal_code, "Обычный домашний рецепт")
    time_display = TIME_OPTIONS.get(time_code, "Не важно")

    # проверка занятости
    if bool(context.user_data.get(BUSY)):
        return await query.message.reply_text("⏳ Я уже генерирую рецепт — подождите немного.")
    context.user_data[BUSY] = True

    try:
        # показываем баннер с информацией о цели и времени
        await query.message.edit_text(
            ai_progress_text(subtitle=f"Цель: <i>{goal_name}</i>, Время: <i>{time_display}</i>"),
            parse_mode=ParseMode.HTML
        )

        # добавляем цель и время в запрос к ИИ
        items_with_goal_and_time = [f"Цель: {goal_name}", f"Время готовки: {time_display}"] + items
        reply = await AI.parse_ingredients(items_with_goal_and_time)

        # форматируем результат
        pretty = format_recipe_for_telegram(reply)

        # сохраняем для кнопки «Сгенерировать другой»
        context.user_data[GOAL_CODE] = goal_code
        context.user_data[SELECTED_TIME] = time_code
        context.user_data[LAST_GENERATED_RECIPE] = {
            "text": reply,
            "ingredients": items,
            "title": items[0] if items else "Рецепт"
        }
        """Создает share-ссылку для рецепта"""
        last_recipe = context.user_data.get(LAST_GENERATED_RECIPE)

        if not last_recipe:
            return await query.message.edit_text(
                "Нет рецепта для отправки.",
                reply_markup=after_recipe_menu(share_url=None)
            )

        # Обрезаем текст рецепта для ссылки (Telegram имеет ограничения)
        recipe_preview = last_recipe['text'][:2000] + "..." if len(last_recipe['text']) > 2000 else last_recipe[
            'text']

        # Создаем текст для шаринга
        share_text = f"🍳 {last_recipe['title']}\n\n{recipe_preview}\n\n✨ Рецепт от @Cook_Br1o_bot"

        # Кодируем текст для URL
        import urllib.parse
        encoded_text = urllib.parse.quote(share_text)
        print(encoded_text)
        # Создаем Telegram share ссылку
        share_url = f"https://t.me/share/url?url=https://t.me/Cook_Br1o_bot&text={encoded_text}"

        # заменяем баннер на готовый рецепт
        await query.message.edit_text(
            pretty,
            reply_markup=after_recipe_menu(share_url=share_url),
            link_preview_options=DEFAULT_TRUE,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False
        )

    except Exception as e:
        logger.error(e)
        await query.message.edit_text("⚠️ Возникла ошибка при запросе генерации рецепта.")
    finally:
        context.user_data[BUSY] = False

    return None

async def handle_goal_selection(goal_code: str, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор цели и показывает выбор времени"""
    goal_name = GOALS.get(goal_code, "Обычный домашний рецепт")
    context.user_data[GOAL_CODE] = goal_code  # Сохраняем выбранную цель

    items = context.user_data.get(SESSION_ITEMS, [])
    items_text = "\n".join([f"• {smart_capitalize(item)}" for item in items[:5]])
    if len(items) > 5:
        items_text += f"\n• ... и ещё {len(items) - 5} продуктов"

    # ДОБАВЛЯЕМ ЭМОДЗИ ДЛЯ КАЖДОЙ ЦЕЛИ
    goal_emojis = {
        "goal_lose": "💪",  # Похудеть
        "goal_pp": "🥑",  # ПП
        "goal_fast": "⚡️",  # Быстро
        "goal_normal": "🍲",  # Обычные
        "goal_vegan": "🥦",  # Веган
        "goal_keto": "🥚"  # Кето-питание
    }

    goal_emoji = goal_emojis.get(goal_code, "🎯")

    # ⬇️⬇️⬇️ ВОТ ЗДЕСЬ ИСПРАВЛЕНИЕ - ДОБАВЛЯЕМ {goal_name} ⬇️⬇️⬇️
    await query.message.edit_text(
        f"🍳 <b>Ваши продукты</b> ({len(items)} шт.):\n\n"
        f"{items_text}\n\n"
        f"{goal_emoji} <b>Цель питания:</b> {goal_name}\n\n"  # ← ТЕПЕРЬ ЗДЕСЬ БУДЕТ "Похудеть", "ПП" и т.д.
        f"⏰ <b>Выберите время готовки:</b>",
        reply_markup=time_selection_menu(),
        parse_mode=ParseMode.HTML
    )

async def handle_time_selection(time_code: str, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор времени готовки и запускает генерацию рецепта"""
    time_display = TIME_OPTIONS.get(time_code, "Не важно")
    context.user_data[SELECTED_TIME] = time_code

    # Получаем сохранённую цель
    goal_code = context.user_data.get(GOAL_CODE, "goal_normal")

    # Запускаем генерацию рецепта с целью и временем
    await goal_recipe_choice_with_time(goal_code, time_code, query, context)

async def back_to_goal_selection(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к выбору цели питания"""
    items = context.user_data.get(SESSION_ITEMS, [])
    items_text = "\n".join([f"• {smart_capitalize(item)}" for item in items[:5]])
    if len(items) > 5:
        items_text += f"\n• ... и ещё {len(items) - 5} продуктов"

    await query.message.edit_text(
        f"🍳 <b>Ваши продукты</b> ({len(items)} шт.):\n\n"
        f"{items_text}\n\n"
        f"🎯 <b>Выберите цель питания:</b>",
        reply_markup=goal_choice_menu(),
        parse_mode=ParseMode.HTML
    )

async def my_recipes(query: CallbackQuery | None):
    """Показывает сохраненные рецепты пользователя"""
    recipes = storage.list_saved_recipes(query.from_user.id)

    if not recipes:
        return await query.message.edit_text(
            "📚 <b>Мои рецепты</b>\n\n"
            "У вас пока нет сохраненных рецептов.\n"
            "Сохраняйте понравившиеся рецепты после генерации!",
            reply_markup=after_recipe_menu(share_url=None),
            parse_mode='HTML'
        )

    # Показываем первый рецепт из списка с навигацией
    recipe = recipes[0]
    text = f"📚 <b>Мои рецепты</b> ({len(recipes)} шт.)\n\n"
    text += f"<b>{recipe['title']}</b>\n\n"
    text += recipe['text'][:1000] + "..." if len(recipe['text']) > 1000 else recipe['text']

    await query.message.edit_text(
        text,
        reply_markup=after_recipe_menu(share_url=None),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

async def share_recipe(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    """Функция для шаринга рецепта"""
    last_recipe = context.user_data.get(LAST_GENERATED_RECIPE)

    if not last_recipe:
        return await query.message.reply_text(
            "Нет рецепта для поделиться. Сначала получите рецепт.",
            reply_markup=main_menu()
        )

    # Создаем клавиатуру для шаринга как на скриншоте "поделится 1.jpg"
    share_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Отправить другу", callback_data="send_to_friend")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_recipe")]
    ])

    await query.message.edit_text(
        "📤 <b>Поделись этим рецептом:</b>",
        reply_markup=share_keyboard,
        parse_mode='HTML'
    )

async def change_products(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к изменению списка продуктов"""
    context.user_data[SESSION_ITEMS] = []
    context.user_data[APPEND_MODE] = False
    context.user_data[AWAIT_MANUAL] = True

    await query.message.edit_text(
        "🔄 <b>Изменить продукты</b>\n\n"
        "Введите новый список продуктов через запятую:\n\n"
        "Пример: курица, рис, лук, морковь",
        reply_markup=photoback_submenu(),
        parse_mode='HTML'
    )


async def send_to_friend(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    """Создает share-ссылку для рецепта"""
    last_recipe = context.user_data.get(LAST_GENERATED_RECIPE)

    if not last_recipe:
        return await query.message.edit_text(
            "Нет рецепта для отправки.",
            reply_markup=after_recipe_menu(share_url=None)
        )

    # Обрезаем текст рецепта для ссылки (Telegram имеет ограничения)
    recipe_preview = last_recipe['text'][:200] + "..." if len(last_recipe['text']) > 200 else last_recipe['text']

    # Создаем текст для шаринга
    share_text = f"🍳 {last_recipe['title']}\n\n{recipe_preview}\n\n✨ Рецепт от @Cook_Br1o_bot"

    # Кодируем текст для URL
    import urllib.parse
    encoded_text = urllib.parse.quote(share_text)

    # Создаем Telegram share ссылку
    share_url = f"https://t.me/share/url?url=https://t.me/Cook_Br1o_bot&text={encoded_text}"

    # Создаем кнопку для шаринга
    share_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Поделиться рецептом", url=share_url)],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_share")]
    ])

    await query.message.edit_text(
        "📤 <b>Поделиться рецептом</b>\n\n"
        "Нажмите кнопку ниже, чтобы поделиться этим рецептом с друзьями в Telegram:",
        reply_markup=share_keyboard,
        parse_mode='HTML'
    )