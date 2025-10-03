from datetime import datetime
from typing import Any


class RecipeEntity:

    def __init__(self, id=None,
                 user_id=None,
                 name=None,
                 ingredients=None,
                 cooking_method=None,
                 cooking_time=None,
                 difficulty=None,
                 kcal=None,
                 pfc=None,
                 create_datetime=None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.ingredients = ingredients
        self.cooking_method = cooking_method
        self.cooking_time = cooking_time
        self.difficulty = difficulty
        self.kcal = kcal
        self.pfc = pfc
        self.create_datetime = create_datetime

    @staticmethod
    def from_row(row: dict[str, Any]):
        return RecipeEntity(
            id=row['id'],
            user_id=row['user_id'],
            name=row['recipe_name'],
            ingredients=row['recipe_ingredients'],
            cooking_method=row['recipe_cooking_method'],
            cooking_time=row['recipe_cooking_time'],
            difficulty=row['recipe_difficulty'],
            kcal=row['recipe_kcal'],
            pfc=row['recipe_pfc'],
            create_datetime=datetime.fromisoformat(row['create_datetime'])
        )

    @staticmethod
    def from_rows(rows: list[dict[str, Any]]):
        return [RecipeEntity.from_row(row) for row in rows]
