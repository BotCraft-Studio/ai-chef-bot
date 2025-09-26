import importlib.util
import os

from pymongo import MongoClient

from app.config import DB_URI, DB_NAME, ENABLE_MIGRATIONS, MIGRATIONS_FOLDER, MIGRATIONS_LOG_COLLECTION


# Функция загрузки файла миграции в роли модуля
def load_migration(file_path):
    spec = importlib.util.spec_from_file_location("migration_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def manage_migrations():
    """
    Функция загружает и применяет файлы миграций в директории,
    которая указана в качестве значения для переменной MIGRATIONS_FOLDER
    """

    if ENABLE_MIGRATIONS:
        print("Внимание: Миграции включены!")

        # Подключение к MongoDB
        client = MongoClient(DB_URI)
        db = client[DB_NAME]

        # Коллекция для логов миграций
        migrations_collection = db[MIGRATIONS_LOG_COLLECTION]

        # Получаем список файлов миграций
        files = sorted(os.listdir(MIGRATIONS_FOLDER))
        for filename in files:
            if filename != "__init__.py" and filename.endswith('.py'):
                file_path = os.path.join(MIGRATIONS_FOLDER, filename)
                migration_name = filename[:-3]

                # Проверяем, не выполнена ли миграция ранее
                if migrations_collection.find_one({'name': migration_name}):
                    print(f"Миграция {migration_name} уже выполнена.")
                    continue

                # Загружаем миграцию
                migration_module = load_migration(file_path)
                # Выполняем функцию миграции, например, `up()`
                if hasattr(migration_module, 'up'):
                    print(f"Запуск миграции {migration_name}...")
                    migration_module.up(db)
                    # Записываем в лог, что миграция выполнена
                    migrations_collection.insert_one({'name': migration_name})
                    print(f"Миграция {migration_name} выполнена.")
                else:
                    print(f"Миграция {migration_name} не содержит функцию 'up()'.")

        client.close()
    else:
        print("Внимание: Миграции отключены!")


if __name__ == "__main__":
    manage_migrations()
