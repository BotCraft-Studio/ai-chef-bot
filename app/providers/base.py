from abc import ABC, abstractmethod

class AIProvider(ABC):
    @abstractmethod
    async def parse_ingredients(self, image_bytes: bytes) -> list[str]:
        ...

    @abstractmethod
    async def recipe_with_macros(self, ingredients: list[str]) -> str:
        ...
