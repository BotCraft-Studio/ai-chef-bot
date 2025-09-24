from mongodb_migrations.base import BaseMigration


class Migration(BaseMigration):
    def upgrade(self):
        self.db.create_collection(
            "users",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["id", "create_datetime"],
                    "properties": {
                        "id": {
                            "bsonType": "string",
                            "description": "ID пользователя"
                        },
                        "login": {
                            "bsonType": "string",
                            "description": "Логин пользователя"
                        },
                        "name": {
                            "bsonType": "string",
                            "description": "Имя в профиле пользователя"
                        },
                        "age": {
                            "bsonType": "int",
                            "description": "Возраст пользователя"
                        },
                        "sex": {
                            "bsonType": "string",
                            "description": "Пол пользователя",
                            "maxLength": 1
                        },
                        "is_premium": {
                            "bsonType": "bool",
                            "description": "Пользователь ТГ-премиум"
                        },
                        "is_pro": {
                            "bsonType": "bool",
                            "description": "Пользователь платной подписки"
                        },
                        "pro_create_date": {
                            "bsonType": "date",
                            "description": "Дата оформления платной подписки"
                        },
                        "pro_expiration_date": {
                            "bsonType": "date",
                            "description": "Дата истечения платной подписки"
                        },
                        "create_datetime": {
                            "bsonType": "date",
                            "description": "Дата начала использования бота"
                        },
                        "update_datetime": {
                            "bsonType": "date",
                            "description": "Дата обновления записи"
                        },
                    }
                }
            }
        )
        print("Таблица 'users' создана")

    def downgrade(self):
        self.db.drop_collection("users")
