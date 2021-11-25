from persianmeme.models import User
from persianmeme.classes import User as UserClass


def handler(text: str, user: UserClass):
    try:
        user.database.temp_user_id = int(text)
    except (ValueError, TypeError):
        user.send_message(user.translate('invalid_user_id'))
    else:
        user.database.menu = User.Menu.ADMIN_MESSAGE_USER
        user.database.back_menu = 'chat_id'
        user.send_message(user.translate('message'))
