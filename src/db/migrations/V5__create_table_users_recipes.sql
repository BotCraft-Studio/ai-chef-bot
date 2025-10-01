-- Таблица для хранения рецептов пользователей
SET search_path TO dev;

CREATE TABLE IF NOT EXISTS users_recipes (
    id                    SERIAL PRIMARY KEY,
    user_id               BIGINT NOT NULL,
    recipe_name           TEXT,
    recipe_ingredients    TEXT[],
    recipe_cooking_method TEXT,
    recipe_cooking_time   INTEGER,
    recipe_difficulty     INTEGER,
    recipe_kcal           INTEGER,
    recipe_pfc            INT[],
    create_datetime       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Создание индекса для ускорения поиска по полю user_id
CREATE INDEX idx_user_id ON users_recipes (user_id);

COMMENT ON COLUMN users_recipes.id IS                    'ID записи';
COMMENT ON COLUMN users_recipes.user_id IS               'ID пользователя';
COMMENT ON COLUMN users_recipes.recipe_name IS           'Название рецепта';
COMMENT ON COLUMN users_recipes.recipe_ingredients IS    'Ингредиенты для рецепта';
COMMENT ON COLUMN users_recipes.recipe_cooking_method IS 'Способ приготовления рецепта';
COMMENT ON COLUMN users_recipes.recipe_cooking_time IS   'Время приготовления рецепта';
COMMENT ON COLUMN users_recipes.recipe_difficulty IS     'Сложность рецепта';
COMMENT ON COLUMN users_recipes.recipe_kcal IS           'Калорийность рецепта';
COMMENT ON COLUMN users_recipes.recipe_pfc IS            'Б/Ж/У рецепта';
COMMENT ON COLUMN users_recipes.create_datetime IS       'Дата создания записи';
