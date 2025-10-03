"""
Модуль отвечает за обработку запросов, поступающих от пользователя
"""

import datetime
import html
import logging
import re

from telegram import Update, CallbackQuery
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import storage

from utils.formatting import format_final_recipe
from utils.query_utils import smart_capitalize, MY_RECIPES, MY_SUBSCRIBE, MAIN_MENU
from keyboards import main_menu, goal_submenu, after_recipe_menu, profile_menu, premium_menu, textback_submenu, photoback_submenu, time_selection_menu, goal_choice_menu, subscription_menu_pro, subscription_menu_lite
from providers.gigachat import GigaChatText
from utils.bot_utils import APPEND_MODE, SESSION_ITEMS, AWAIT_MANUAL, BUSY, GOAL_CODE, LAST_GENERATED_RECIPE, SELECTED_TIME, TIME_OPTIONS
from utils.goal_utils import GOALS
from utils import query_utils

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
        reply = await AI.parse_ingredients([recipe_name])
        pretty = format_final_recipe(reply, "Обычные")   # <-- ВАЖНО: форматируем под «Обычные»

        await query.message.edit_text(
            f"✨ Рецепт дня!\n\n{pretty}",
            reply_markup=main_menu(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception:
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
        "Например: Cыр, помидоры, оливковое масло"
    )


async def goal_recipe(query: CallbackQuery | None):
    text = (
        "Добро пожаловать в AI-Chef! 👨‍🍳\n\n"
        "Я ваш персональный шеф-повар с искусственным интеллектом!\n\n"
        "✨ Что я умею:\n\n"
        "• Создавать рецепты из ваших продуктов\n"
        "• Рассчитывать точное КБЖУ для каждой порции\n"
        "• Предлагать сезонные рецепты дня\n"
        "• Помогать достигать ваших целей питания\n\n"
        "🎯 Выберите способ ввода продуктов:"
    )
    await query.message.edit_text(text, reply_markup=goal_submenu())

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
        "⌨️ Введите продукты через запятую:\n\nПример: Курица, рис, лук, морковь",
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
        pretty = format_final_recipe(reply, goal_name)

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
            reply_markup=after_recipe_menu(),
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
    last_ingredients = context.user_data.get(LAST_GENERATED_RECIPE)

    if not last_ingredients:
        return await query.message.edit_text(
            "Нет последнего списка ингредиентов. Сначала введите продукты.",
            reply_markup=main_menu()
        )

    if context.user_data.get(BUSY):
        return await query.message.reply_text("⏳ Я уже генерирую рецепт — подождите немного.")
    context.user_data[BUSY] = True

    try:
        reply = await AI.parse_ingredients(last_ingredients)

        goal_code = context.user_data.get(GOAL_CODE, "goal_normal")
        from utils.goal_utils import GOALS
        goal_name = GOALS.get(goal_code, "Обычные")

        pretty = format_final_recipe(reply, goal_name)
    except Exception as e:
        return await query.message.edit_text(f"Ошибка генерации: {e}", reply_markup=main_menu())
    finally:
        context.user_data[BUSY] = False

    context.user_data[LAST_GENERATED_RECIPE] = {
        "text": pretty,
        "ingredients": last_ingredients,
        "title": last_ingredients[0] if last_ingredients else "Рецепт"
    }

    await query.message.edit_text(
        reply,
        reply_markup=after_recipe_menu(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

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
    await query.message.reply_text("✅ Рецепт сохранён в вашем списке.", reply_markup=profile_menu())

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
    text = (
        "⚡️ <b>ПРЕИМУЩЕСТВА PRO подписки</b>:\n\n"
        "🍽 <b>1. Все режимы питания без ограничений</b>\n"
        "⤷ Хочешь похудеть, сидишь на кето-диете или просто мало времени? — выбирай нужную категорию, а я подстроюсь.\n\n"
        "📜 <b>2. Генерируй рецепты без лимита</b>\n"
        "⤷ Забудь про ограничение 1 рецепт в день. Генерируй сколько хочешь — хоть 50 штук за раз!\n\n"
        "❤️ <b>3. Сохраняй до 20 любимых рецептов</b>\n"
        "⤷ Понравилось блюдо? Сохрани! В премиуме — в 4 раза больше места в избранном.\n\n"
        "🥦 <b>4. Анализ КБЖУ по каждому рецепту</b>\n"
        "⤷ Устал считать самостоятельно? Сделаю это за тебя!\n\n"
        "🚀 <b>5. Скорость вне очереди</b>\n"
        "⤷ Когда я перегружен, ты получаешь приоритетный ответ первым.\n\n"
        "🔥 <b>Стоимость:</b> 1 ₽ за 3 дня — дальше 349 ₽/мес\n"
        "Меньше, чем за чашку кофе ☕️ — и ты больше никогда не будешь думать, что приготовить.\n\n"
        "❌ Отменить подписку можно в любой момент в личном кабинете.\n\n"
        "Для оплаты свяжитесь с @администратор"
    )

    await query.message.edit_text(
        text,
        reply_markup=premium_menu(),
        parse_mode="HTML",
        disable_web_page_preview=True
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
        pretty = format_final_recipe(reply, goal_name)

        # сохраняем для кнопки «Сгенерировать другой»
        context.user_data[GOAL_CODE] = goal_code
        context.user_data[SELECTED_TIME] = time_code
        context.user_data[LAST_GENERATED_RECIPE] = {
            "text": reply,
            "ingredients": items,
            "title": items[0] if items else "Рецепт"
        }

        # заменяем баннер на готовый рецепт
        await query.message.edit_text(
            pretty,
            reply_markup=after_recipe_menu(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(e)
        await query.message.edit_text("⚠️ Возникла ошибка при запросе генерации рецепта.")
    finally:
        context.user_data[BUSY] = False

    return None

async def handle_goal_selection(goal_code: str, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор цели и показывает меню времени"""
    # 1) Сохраняем выбранную цель в user_data
    context.user_data[GOAL_CODE] = goal_code

    # 2) Человекочитаемое имя цели
    goal_name = GOALS.get(goal_code, "Обычные")

    # 3) Забираем продукты из сессии (их туда положил ваш пречек после ввода/фото)
    items = context.user_data.get(SESSION_ITEMS, [])
    if not items:
        # если вдруг пусто — подскажем пользователю
        return await query.message.edit_text(
            "Не вижу ваших продуктов. Введите список или отправьте фото.",
        )

    # 4) Красивый список (первые 5 пунктов + счётчик)
    items_text = "\n".join([f"• {smart_capitalize(item)}" for item in items[:5]])
    if len(items) > 5:
        items_text += f"\n• ... и ещё {len(items) - 5} продукт(а/ов)"

    # 5) Эмодзи под цель (для UI)
    goal_emojis = {
        "goal_lose": "💪",
        "goal_pp": "🥑",
        "goal_fast": "⚡️",
        "goal_normal": "🍲",
        "goal_vegan": "🥦",
        "goal_keto": "🥚",
    }
    goal_emoji = goal_emojis.get(goal_code, "🎯")

    # 6) Переходим к выбору времени
    await query.message.edit_text(
        f"🍳 <b>Ваши продукты</b> ({len(items)} шт.):\n\n"
        f"{items_text}\n\n"
        f"{goal_emoji} <b>Цель питания:</b> {goal_name}\n\n"
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

# --- ПРОФИЛЬ: Мои рецепты ---
async def profile_my_recipes(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):

    user_id = query.from_user.id
    try:
        recipes = storage.list_saved_recipes(user_id) 
    except Exception:
        recipes = []

    if not recipes:
        txt = (
            "📖 <b>Мои рецепты</b>\n\n"
            "Пока пусто. Сохраняйте понравившиеся рецепты кнопкой «❤️ В избранное»."
        )
        return await query.message.edit_text(
            txt, parse_mode=ParseMode.HTML, reply_markup=subscription_menu_pro()
        )

    lines = []
    for i, r in enumerate(recipes[:5], start=1):
        title = r.get("title") or f"Рецепт #{i}"
        lines.append(f"{i}. {title}")

    txt = "📖 <b>Мои рецепты</b>\n\n" + "\n".join(lines)
    await query.message.edit_text(
        txt, parse_mode=ParseMode.HTML, reply_markup=subscription_menu_pro()
    )

# --- ПРОФИЛЬ: Подписка ---
async def profile_subscribe(query: CallbackQuery):

    user_id = query.from_user.id
    try:
        is_pro = storage.user_is_pro(user_id)
    except Exception:
        is_pro = False

    if is_pro:
        txt = (
            "🧾 <b>Моя подписка</b>\n\n"
            "Статус: Активна ✅\n"
            "Активна до: <b>дд.мм.гггг</b>\n"
            
            
            "Преимущества PRO: больше токенов, приоритет, премиум-рецепты."
        )
        kb = subscription_menu_pro()   # только «Назад»
    else:
        txt = (
            "🧾 <b>Моя подписка</b>\n\n"
            "Статус: <b>Lite</b>\n"
            "Ограничения: 2 рецепта в день.\n\n"
            "Повысьте до PRO, чтобы получить больше лимитов и функций."
        )
        kb = subscription_menu_lite()  # «Улучшить до PRO» + «Назад»

    await query.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=kb)

async def back_to_profile(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    text, markup, pm = await build_profile_view(context, user_id)
    await query.message.edit_text(text, reply_markup=markup, parse_mode=pm)

# Нажатие «Улучшить до PRO»
async def subscribe_upgrade(query: CallbackQuery):
    from telegram.constants import ParseMode
    from keyboards import subscription_menu_lite
    txt = (
        "💳 <b>Улучшение до PRO</b>\n\n"
        "Для оформления PRO свяжитесь с администратором: @admin\n"
        "Скоро добавим оплату прямо в боте."
    )
    await query.message.edit_text(txt, parse_mode=ParseMode.HTML, reply_markup=subscription_menu_lite())

async def build_profile_view(context, user_id: int):
    # 1) Статус
    try:
        is_pro = storage.user_is_pro(user_id)
    except Exception:
        is_pro = False
    status = "PRO" if is_pro else "Lite"

    # 2) Счётчики
    try:
        recipes_total = storage.count_recipes(user_id)
    except Exception:
        recipes_total = 0
    try:
        favorites_total = storage.count_favorites(user_id)
    except Exception:
        favorites_total = 0

    # 3) Последние продукты (сначала из сессии, если есть)
    items = context.user_data.get("SESSION_ITEMS") or []
    if not items:
        try:
            rows = storage.list_ingredients(user_id) or []
            items = [name for _, name, _ in rows[:5]]
        except Exception:
            items = []
    last_items_txt = "\n".join(f"• {x}" for x in items[:5]) if items else "—"

    # 4) Текст + клавиатура
    text = (
        "👤 <b>Мой профиль</b>\n\n"
        f"Статус: <b>{status}</b>\n"
        f"Сгенерировано рецептов: <b>{recipes_total}</b>\n"
        f"В избранном: <b>{favorites_total}</b>\n\n"
        f"<b>Последние продукты:</b>\n{last_items_txt}"
    )
    return text, profile_menu(), ParseMode.HTML