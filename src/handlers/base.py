import logging
import re

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from handlers.query_handler import (
    back_to_main_menu,
    buy_pro,
    change_goal,
    clear_ingredients,
    daily_recipe,
    goal_recipe,
    goal_recipe_choice,
    manual_input,
    my_ingredients,
    regenerate_recipe,
    save_recipe,
    upload_photo, 
    back_to_goal_selection, 
    handle_time_selection, 
    handle_goal_selection,
    profile_my_recipes,
    profile_subscribe,
    back_to_profile,
    subscribe_upgrade,
)

from handlers.query_handler import goal_recipe_choice_with_time
from src.keyboards import goal_choice_menu, time_selection_menu
from utils import query_utils
from utils.bot_utils import BUSY, AWAIT_MANUAL, SESSION_ITEMS, APPEND_MODE, TIME_OPTIONS, SELECTED_TIME, GOAL_CODE
from utils.goal_utils import GOALS
from utils.query_utils import MANUAL_INPUT, smart_capitalize

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip() if update.message and update.message.text else ""

    # Если бот занят — предупреждаем
    if bool(context.user_data.get(BUSY)):
        return await update.message.reply_text("⏳ Я сейчас генерирую рецепт — подожди чуть-чуть, пожалуйста.")

    # Принимаем текст ТОЛЬКО если пользователь в режиме ручного ввода
    if bool(context.user_data.get(AWAIT_MANUAL)):
        raw = list((text or "").split(","))
        to_add = normalize_items(raw)  # lower, без дублей
        if not to_add:
            return await update.message.reply_text("Список пуст. Пример: курица, рис, лук")

        # текущая сессия
        session_items = context.user_data.get(SESSION_ITEMS, [])
        append_mode = bool(context.user_data.get(APPEND_MODE))

        if append_mode:
            existing = set(session_items)
            new_only = [i for i in to_add if i not in existing]
            session_items = session_items + new_only
            highlights = set(new_only)
        else:
            session_items = to_add
            highlights = set()

        # сохранить обратно
        context.user_data[SESSION_ITEMS] = session_items
        context.user_data[AWAIT_MANUAL] = False

        # Показать НОВЫЙ пречек (старый остаётся), с пометкой «+» у добавленных
        is_updated = append_mode and bool(highlights)
        precheck = render_precheck(session_items, highlights, updated=is_updated)

        # ⬇️⬇️⬇️ ТЕПЕРЬ СНАЧАЛА ПОКАЗЫВАЕМ ВЫБОР ЦЕЛИ ⬇️⬇️⬇️
        await update.message.reply_text(
            precheck,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=goal_choice_menu()  # ← сразу показываем цели
        )
        return None

    # Иначе — подсказка
    await update.message.reply_text(
        "Чтобы ввести продукты вручную, нажмите кнопку ниже:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⌨️ Ввести продукты вручную", callback_data=MANUAL_INPUT)]
        ])
    )

    return None


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_input = query.data
    user_id = query.from_user.id

    match user_input:
        case query_utils.ADD_INGREDIENT:
            await my_ingredients(query)
        case query_utils.MAIN_MENU:
            await back_to_main_menu(query)

        # Вроде как не используется, не нашел в боте
        case query_utils.BUY_PRO:
            await buy_pro(query)

        case query_utils.DAILY_RECIPE:
            await daily_recipe(query)
        case query_utils.GOAL_RECIPE:
            await goal_recipe(query)
        case query_utils.MANUAL_INPUT:
            await manual_input(query, context)
        case query_utils.REGENERATE_RECIPE:
            await regenerate_recipe(query, context)
        case query_utils.SAVE_RECIPE:
            await save_recipe(user_id, query, context)
        case query_utils.UPLOAD_PHOTO:
            await upload_photo(query)
        case query_utils.BACK_TO_GOAL_SELECTION:
            # Возврат к выбору цели
            await back_to_goal_selection(query, context)
        case query_utils.MY_RECIPES:
            await profile_my_recipes(query, context)
        case query_utils.MY_SUBSCRIBE:
            await profile_subscribe(query)
        case query_utils.BACK_TO_PROFILE:
            await back_to_profile(query, context)
        case query_utils.BUY_PRO:
            await subscribe_upgrade(query)
        case user_input if user_input in TIME_OPTIONS:
            # Обработка выбора времени
            await handle_time_selection(user_input, query, context)
        case _:
            # Случай, когда пользователь выбрал цель рецепта
            if user_input in GOALS:
                # ТЕПЕРЬ ПОСЛЕ ВЫБОРА ЦЕЛИ ПОКАЗЫВАЕМ ВЫБОР ВРЕМЕНИ
                await handle_goal_selection(user_input, query, context)


def normalize_items(raw_items):
    uniq, seen = [], set()
    for x in raw_items:
        s = re.sub(r'\s+', ' ', x).strip(" .,!?:;\"'()[]").strip().lower()
        if s and s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def render_precheck(
        items: list[str],
        highlights: set[str] | None = None,
        updated: bool = False
) -> str:
    highlights = highlights or set()
    pretty = []
    for it in items:
        mark = " + " if it in highlights else ""
        pretty.append(f"•{mark}{smart_capitalize(it)}")
    body = "\n".join(pretty)

    title = "<b>✅ Вот твои обновлённые продукты</b>" if updated else "<b>Вот твои продукты</b>"

    return (
        f"{title} (<i>{len(items)} шт.</i>)\n\n"
        f"{body}\n\n"
        "🎯 <b>Выбери цель</b>: ПП, Обычные и т.д.\n"
        "<i>Подсказка: если чего-то не хватает — нажми «Добавить продукты» и дополни список.</i>"
    )