"""
Модуль отвечает за обработку запросов, поступающих от пользователя
"""

import datetime
import html
import logging
import re

from telegram import CallbackQuery
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import storage
from keyboards import main_menu, goal_submenu, after_recipe_menu, profile_menu, premium_menu
from providers.yandex_vision import YandexRecipes
from utils.bot_utils import APPEND_MODE, SESSION_ITEMS, AWAIT_MANUAL, BUSY, GOAL_CODE, LAST_GENERATED_RECIPE
from utils.goal_utils import GOALS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

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

AI = YandexRecipes()

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
        reply = await AI.recipe_with_macros([recipe_name])
        pretty = format_recipe_for_telegram(reply)

        # 4) Заменяем баннер на готовый рецепт (снова редактируем то же сообщение → вторая анимация)
        await query.message.edit_text(
            f"✨ Рецепт дня!\n\n{pretty}",
            reply_markup=main_menu(),
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
        "📷 Отправьте фото продуктов\n\nСовет: сфотографируйте продукты на светлом фоне для лучшего распознавания")


async def manual_input(query: CallbackQuery | None, context: ContextTypes.DEFAULT_TYPE):
    # чистый лист в СЕССИИ
    context.user_data[SESSION_ITEMS] = []
    context.user_data[APPEND_MODE] = False
    context.user_data[AWAIT_MANUAL] = True

    # ВАЖНО: не edit_text (это замещает пречек), а reply_text — пречек останется!
    await query.message.reply_text(
        "⌨️ Введите продукты через запятую:\n\nПример: курица, рис, лук, морковь"
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
        reply = await AI.recipe_with_macros(items_with_goal)

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
        reply = await AI.recipe_with_macros(last_ingredients)
        pretty = format_recipe_for_telegram(reply)
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
    await query.message.edit_text(
        "💳 <b>Оформление PRO подписки</b>\n\n"
        "Для оплаты свяжитесь с @администратор",
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