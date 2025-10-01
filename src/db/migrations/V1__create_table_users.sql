-- Таблица для хранения информации о пользователях

CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    user_id             BIGINT UNIQUE NOT NULL,
    name                VARCHAR(255),
    login               VARCHAR(255),
    age                 INT,
    sex                 VARCHAR(1),
    is_pro              BOOLEAN DEFAULT FALSE,
    pro_create_date     DATE,
    pro_expiration_date DATE,
    create_datetime     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_datetime     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON COLUMN users.id IS                  'ID записи';
COMMENT ON COLUMN users.user_id IS             'ID пользователя';
COMMENT ON COLUMN users.name IS                'Имя пользователя';
COMMENT ON COLUMN users.login IS               'Логин пользователя';
COMMENT ON COLUMN users.age IS                 'Возраст пользователя';
COMMENT ON COLUMN users.sex IS                 'Пол пользователя';
COMMENT ON COLUMN users.is_pro IS              'Пользователь с платной подпиской';
COMMENT ON COLUMN users.pro_create_date IS     'Дата оформления платной подписки';
COMMENT ON COLUMN users.pro_expiration_date IS 'Дата истечения платной подписки';
COMMENT ON COLUMN users.create_datetime IS     'Дата создания записи';
COMMENT ON COLUMN users.update_datetime IS     'Дата обновления записи';
