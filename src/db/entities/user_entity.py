from telegram import Message, User


class UserEntity:
    def __init__(self,
                 _id=None,
                 user_id=None,
                 name=None,
                 login=None,
                 age=None,
                 sex=None,
                 is_pro=None,
                 pro_create_date=None,
                 pro_expiration_date=None,
                 create_datetime=None,
                 update_datetime=None):
        self.id = _id
        self.user_id = user_id
        self.name = name
        self.login = login
        self.age = age
        self.sex = sex
        self.is_pro = is_pro
        self.pro_create_date = pro_create_date
        self.pro_expiration_date = pro_expiration_date
        self.create_datetime = create_datetime
        self.update_datetime = update_datetime

    @classmethod
    def from_tg_user(cls, user: User, is_pro: bool = False):
        return cls(_id=user.id,
                   name=user.full_name,
                   login=user.username,
                   is_pro=is_pro)
