# app/providers/yandex_vision.py
import os
import json
import aiohttp
from app.config import YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_TIMEOUT

SYS_RECIPE = (
    "Ты шеф-повар и нутриционист. Дай 1 рецепт из списка продуктов.\n"
    "Структура:\nНазвание\nИнгредиенты (с граммами)\nШаги (5–8)\nКБЖУ на порцию (оценка)\nСоветы/замены\n"
    "Отвечай коротко и по делу, без приветствий и лишних фраз."
)

API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


class YandexRecipes:
    def __init__(self):
        if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
            raise RuntimeError("YANDEX_API_KEY и YANDEX_FOLDER_ID обязательны в окружении")

    async def _chat(self, messages: list[dict]) -> str:
        payload = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000",
                "reasoningOptions": {"mode": "DISABLED"}
            },
            "messages": messages,
        }

        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "Content-Type": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=YANDEX_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(API_URL, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()

        # Попробовать получить текст в нескольких вариантах структуры ответа
        try:
            alt = data["result"]["alternatives"][0]["message"]
            # иногда content — строка
            if isinstance(alt.get("content"), str):
                return alt["content"].strip()
            if isinstance(alt.get("text"), str):
                return alt["text"].strip()
            # если content — сложная структура, stringify
            if alt.get("content"):
                return json.dumps(alt["content"], ensure_ascii=False)
        except Exception:
            pass

        try:
            return data["result"]["output"][0]["content"][0]["text"].strip()
        except Exception:
            pass

        # fallback — вернуть весь JSON (для отладки)
        return json.dumps(data, ensure_ascii=False, indent=2)

    async def recipe_with_macros(self, ingredients: list[str]) -> str:
        # user_prompt — то, что получает роль user (включаем список ингредиентов + опции)
        user_prompt = (
            "Составь подробный рецепт из этих продуктов: " + ", ".join(ingredients) +
            ". Если чего-то не хватает — добавь базовые кладовые (масло, соль, перец). "
            "Укажи КБЖУ как ориентировочную оценку. Пиши на русском."
        )
        messages = [
            {"role": "system", "text": SYS_RECIPE},
            {"role": "user", "text": user_prompt}
        ]
        return await self._chat(messages)
