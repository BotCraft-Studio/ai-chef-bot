-- Функция для обновления поля users.update_datetime
CREATE OR REPLACE FUNCTION users_update_datetime()
RETURNS TRIGGER AS $$
BEGIN
    NEW.update_datetime = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер, который вызывает функцию users_update_datetime перед UPDATE
CREATE TRIGGER users_update_datetime
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION users_update_datetime();