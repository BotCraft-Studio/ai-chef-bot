# src/providers/gigachat.py
import aiohttp, base64, time, uuid, json, re
from typing import Optional, List

from src.config import (
    GIGACHAT_BASE_URL, GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET,
    GIGACHAT_SCOPE, GIGACHAT_VERIFY_SSL,
    GIGACHAT_TEXT_MODEL, GIGACHAT_VISION_MODEL,   # 👈 добавили
)
from utils.bot_utils import TIME_LIMITS  # 👈 используем числовой лимит

TOKEN_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

class GigaChatClient:
    """Клиент GigaChat: OAuth (NGW) + chat/completions (gigachat)."""
    def __init__(self):
        if not GIGACHAT_CLIENT_ID or not GIGACHAT_CLIENT_SECRET:
            raise RuntimeError("GIGACHAT_CLIENT_ID/GIGACHAT_CLIENT_SECRET не заданы")
        self._access_token: Optional[str] = None
        self._exp: float = 0.0

    async def _ensure_token(self):
        """Берём access_token по client_credentials на NGW-хосте."""
        if self._access_token and time.time() < self._exp - 60:
            return

        auth = base64.b64encode(f"{GIGACHAT_CLIENT_ID}:{GIGACHAT_CLIENT_SECRET}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
        }
        data = {"scope": GIGACHAT_SCOPE}

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post(
                TOKEN_URL, headers=headers, data=data,
                ssl=(False if not GIGACHAT_VERIFY_SSL else None)
            ) as r:
                txt = await r.text()
                if r.status >= 400:
                    raise RuntimeError(f"OAuth {r.status} {txt}")
                try:
                    js = json.loads(txt)
                except json.JSONDecodeError:
                    raise RuntimeError(f"OAuth decode error: {txt[:400]}")


        self._access_token = js.get("access_token")
        # в ЛК пишут ~30 минут. если приходит expires_at — используем его.
        self._exp = time.time() + int(js.get("expires_at") or 1800)

    async def _post_json(self, path: str, payload: dict) -> dict:
        """POST на gigachat.../api/v1 с таймаутом и авто-обновлением токена при 401."""
        await self._ensure_token()
        timeout = aiohttp.ClientTimeout(total=30)
        url = f"{GIGACHAT_BASE_URL}{path}"

        async def _do(headers):
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.post(url, headers=headers, json=payload,
                                ssl=(False if not GIGACHAT_VERIFY_SSL else None)) as r:
                    txt = await r.text()
                    if r.status == 401:
                        raise PermissionError("unauthorized", txt)
                    if r.status >= 400:
                        raise RuntimeError(f"{r.status} {txt}")
                    return json.loads(txt)

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            return await _do(headers)
        except PermissionError:
            # токен устарел — обновим и повторим один раз
            await self._ensure_token()
            headers["Authorization"] = f"Bearer {self._access_token}"
            return await _do(headers)

    async def _upload_file(self, image_bytes: bytes, filename: str = "photo.jpg") -> dict:
        await self._ensure_token()
        headers = {"Authorization": f"Bearer {self._access_token}"}

        form = aiohttp.FormData()
        form.add_field("purpose", "general")
        form.add_field("file", image_bytes, filename=filename, content_type="image/jpeg")

        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.post(f"{GIGACHAT_BASE_URL}/files",
                            headers=headers, data=form,
                            ssl=(False if not GIGACHAT_VERIFY_SSL else None)) as r:
                txt = await r.text()
                if r.status >= 400:
                    raise RuntimeError(f"Upload {r.status} {txt}")
                try:
                    return json.loads(txt)
                except json.JSONDecodeError:
                    raise RuntimeError(f"Upload decode error: {txt[:400]}")


class GigaChatText(GigaChatClient):
    GOAL_GUIDELINES = {
        "Похудеть": "Дефицит калорий, без сахара, минимум масла. Белка 25–35% калорий, жарку заменить запеканием/тушением.",
        "ПП (правильное питание)": "Сбалансируй БЖУ, цельные продукты, минимум обработки, без сахара и трансжиров.",
        "Быстро": "Готовка ≤ 20 минут, минимум шагов и посуды.",
        "Обычные": "Классический домашний рецепт без строгих ограничений.",
        "Веган": "Полностью без продуктов животного происхождения.",
        "Кето-питание": "Углеводы <10% калорий, жиры высокие, без сахара/крахмалистых."
    }

    async def parse_ingredients(self, ingredients: list[str]) -> str:
        # 1) Достаём служебные строки
        goal_line = next((x for x in ingredients if x.startswith("Цель:")), None)
        time_line = next((x for x in ingredients if x.startswith("Время готовки:")), None)

        goal_name = goal_line.split(":", 1)[1].strip() if goal_line else "Обычные"
        time_text = time_line.split(":", 1)[1].strip() if time_line else "Не важно"

        # 2) Чистые продукты
        pure_items = [x for x in ingredients if not x.startswith(("Цель:", "Время готовки:"))]

        # 3) Лимит времени (в минутах) по time_text → по кнопке, сохранённой в контексте
        # Т.к. в этот метод приходит только текст "До 15 мин"/"Не важно", нам достаточно выдрать число из текста:
        import re
        match = re.search(r"(\d+)", time_text)
        time_limit = int(match.group(1)) if match else None  # None = нет лимита

        # 4) Правила под цель
        rules = self.GOAL_GUIDELINES.get(goal_name, "Готовь обычный домашний рецепт.")

        # 5) Жёсткие требования к формату и времени
        hard_time_rule = (
            f"СОБЛЮДАЙ общий лимит времени: не больше {time_limit} минут. "
            "Если какое-то действие обычно дольше — сократи/упрости (мельче нарезка, параллельные шаги, полуфабрикаты типа готового риса в пакетиках). "
            "Если всё равно не укладываешься — предложи быстрые замены прямо в шаге."
        ) if time_limit else "Если возможно, оценивай время максимально кратко."

        user_prompt = (
            "Составь подробный РЕЦЕПТ из этих продуктов: " + ", ".join(pure_items) + ". "
            f"Цель: {goal_name}. {rules} "
            f"Время готовки (предпочтение): {time_text}. {hard_time_rule} "
            "Если чего-то не хватает — добавь базовые кладовые (масло, соль, перец). "
            "Пиши на русском.\n\n"
            "СТРОГОЙ ФОРМАТ ОТВЕТА:\n"
            "1) Название: <кратко>\n"
            "2) Ингредиенты (на 2–4 порции): список с граммами\n"
            "3) Шаги: 5–8 пунктов. Указывай длительность ключевых шагов (например, «обжарить 3–4 мин»). Разрешены параллельные действия.\n"
            "4) ⏱ Итого время: <число> минут\n"
            "5) КБЖУ на порцию: Калории, Белки, Жиры, Углеводы (оценочно)\n"
            "6) 🎯 Соответствие цели: 1–2 предложения (почему рецепт подходит цели)\n"
            "7) Советы/замены: 2–4 пункта\n"
        )

        payload = {
            "model": GIGACHAT_TEXT_MODEL,
            "messages": [
                {"role": "system", "content": "Ты шеф-повар и нутриционист. Пиши чётко, без воды."},
                {"role": "user", "content": user_prompt}
            ],
            "maxTokens": 900,
            "profanity_check": True,
            "temperature": 0.4,
        }

        js = await self._post_json("/chat/completions", payload)
        return (js.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        
class GigaChatVision(GigaChatClient):
    async def parse_ingredients(self, image_bytes: bytes) -> list[str]:
        up = await self._upload_file(image_bytes, filename="photo.jpg")
        file_id = up.get("id") or up.get("file_id")
        if not file_id:
            raise RuntimeError(f"Нет id у загруженного файла: {up}")

        payload = {
            "model": GIGACHAT_VISION_MODEL, # 👈 vision-модель
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Какие продукты изображены на фото? Верни ЧЁТКИЙ список, по одному на строку.\n\n"
                        "пример:\n- Говядина\n- Помидоры\n- Лук\n- Хлеб"
                    ),
                    "attachments": [file_id] # 👈 список ID
                }
            ],
            "maxTokens": 600,
            "profanity_check": True
        }
        js = await self._post_json("/chat/completions", payload)
        text = (js.get("choices") or [{}])[0].get("message", {}).get("content", "")
        lines = [re.sub(r"^[-•*]\s*|\d+[.)]\s*", "", s).strip() for s in str(text).splitlines()]
        return [s for s in lines if s]
