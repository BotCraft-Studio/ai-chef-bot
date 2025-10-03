-- Таблица для хранения ингредиентов пользователей
SET search_path TO dev;

CREATE TABLE IF NOT EXISTS users_ingredients (
    id                  SERIAL PRIMARY KEY,
    user_id             BIGINT UNIQUE NOT NULL,
    ingredients         TEXT[] DEFAULT '{}',
    update_datetime     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

COMMENT ON COLUMN users_ingredients.id IS                   'ID записи';
COMMENT ON COLUMN users_ingredients.user_id IS              'ID пользователя';
COMMENT ON COLUMN users_ingredients.ingredients IS          'Список ингредиентов пользователя';
COMMENT ON COLUMN users_ingredients.update_datetime IS      'Дата обновления записи';
