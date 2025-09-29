import logging

import psycopg
from psycopg import connect, Connection

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from db.entities.recipe_entity import RecipeEntity
from db.entities.user_entity import UserEntity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_connection() -> Connection:
    try:
        return connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    except psycopg.Error as e:
        logger.error("Возникла ошибка во время попытки открыть соединение с БД:")
        raise e


def add_user(user: UserEntity) -> int:
    con = get_connection()
    try:
        with con:
            with con.cursor() as cur:
                # Добавляем запись в таблицу пользователй
                cur.execute(
                    """
                    INSERT INTO users (user_id, name, login)
                    VALUES (%s, %s, %s)
                    RETURNING user_id;
                    """,
                    (user.id, user.name, user.login)
                )
                user_id = cur.fetchone()
                # Добавляем запись в таблицу с ингредиентами пользователей
                # По дефолту инициализируем список ингредиентов пользователя как пустой массив
                cur.execute(
                    """
                    INSERT INTO users_ingredients (user_id, ingredients)
                    VALUES (%s, %s)
                    """,
                    (user.id, [])
                )
                return user_id
    except psycopg.Error as e:
        logger.error("Ошибка при добавлении пользователя:", exc_info=True)
        raise e


def get_user_ingredients(user_id: int):
    con = get_connection()
    with con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT ingredients
                FROM users_ingredients
                WHERE user_id = %s
                """,
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                return []


def add_ingredients(user_id: int, new_ingredients: list[str]) -> list[str]:
    con = get_connection()
    with con:
        with con.cursor() as cur:
            # Обновляем список, объединяя существующий и новые ингредиенты (только уникальные ингредиенты, без дублей)
            cur.execute(
                """
                UPDATE users_ingredients
                SET ingredients = (
                    SELECT ARRAY(
                        SELECT DISTINCT element
                        FROM unnest(ingredients || %s) AS element
                    )
                )
                WHERE user_id = %s
                RETURNING ingredients;
                """,
                (new_ingredients, user_id)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                return new_ingredients


def clear_ingredients(user_id: int) -> None:
    con = get_connection()
    with con:
        with con.cursor() as cur:
            cur.execute(
                """
                UPDATE users_ingredients
                SET ingredients = []
                WHERE user_id = %s
                """,
                (user_id,)
            )


def get_recipes(user_id: int) -> list[RecipeEntity]:
    con = get_connection()
    with con:
        with con.cursor() as cur:
            cur.execute(
                """
                    SELECT *
                    FROM users_recipes
                    WHERE user_id = %s
                """,
                (user_id,)
            )
            rows = cur.fetchall()
            if rows:
                return RecipeEntity.from_rows(rows)
            else:
                return []


def add_recipe(user_id: int, recipe: RecipeEntity) -> int:
    con = get_connection()
    with con:
        with con.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users_recipes (user_id, 
                                           recipe_name, 
                                           recipe_ingredients, 
                                           recipe_cooking_method, 
                                           recipe_cooking_time, 
                                           recipe_difficulty, 
                                           recipe_kcal, 
                                           recipe_pfc)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (user_id,
                 recipe.name,
                 recipe.ingredients,
                 recipe.cooking_method,
                 recipe.cooking_time,
                 recipe.difficulty,
                 recipe.kcal,
                 recipe.pfc)
            )
            row = cur.fetchone()
            if row:
                return row[0]
            else:
                return -1
