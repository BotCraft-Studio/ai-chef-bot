import base64
from openai import OpenAI
from app.config import YANDEX_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT, DEEPSEEK_BASE_URL

SYS_PARSE = (
    "Ты кулинарный ассистент. По изображению определи СПИСОК ПРОДУКТОВ. "
    "Верни только пункты списка на русском: 'курица', 'рис', 'лук'. Без описаний."
)

SYS_RECIPE = (
    "Ты шеф-повар и нутриционист. Дай 1 рецепт из списка продуктов. "
    "Структура:\nНазвание\nИнгредиенты (с граммами)\nШаги (5–8)\nКБЖУ на порцию (оценка)\nСоветы/замены"
)

class OpenAIVision:
    def __init__(self):
        if not YANDEX_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.client = OpenAI(api_key=YANDEX_API_KEY,base_url=DEEPSEEK_BASE_URL)

    async def _chat(self, messages):
        resp = await self.client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.6,
        )
        return resp.choices[0].message.content.strip()

    async def parse_ingredients(self, image_bytes: bytes) -> list[str]:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        msgs = [
            {"role": "system", "content": SYS_PARSE},
            {"role": "user", "content": [
                {"type": "text", "text": "Определи продукты на фото."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]},
        ]
        txt = await self._chat(msgs)
        items = [x.strip(" -*•\t\r\n") for x in txt.splitlines()]
        items = [x for x in items if x and len(x.split()) <= 4]
        seen, out = set(), []
        for x in items:
            xl = x.lower()
            if xl not in seen:
                seen.add(xl)
                out.append(x)
        return out[:20]

    async def recipe_with_macros(self, ingredients: list[str]) -> str:
        prompt = (
            "Составь рецепт из этих продуктов: " + ", ".join(ingredients) + ". "
            "Если чего-то не хватает — добавь базовые кладовые (масло, соль). "
            "Укажи КБЖУ как ориентировочную оценку."
        )
        return await self._chat([
            {"role": "system", "content": SYS_RECIPE},
            {"role": "user", "content": prompt},
        ])
