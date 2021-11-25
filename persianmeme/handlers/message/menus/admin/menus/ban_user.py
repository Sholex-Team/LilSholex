from persianmeme.functions import change_user_status
from persianmeme.keyboards import admin
from persianmeme.models import User
from persianmeme.classes import User as UserClass


def handler(text: str, user: UserClass, ban_mode: User.Status):
    try:
        user_id = int(text)
    except (ValueError, TypeError):
        user.send_message(user.translate('invalid_user_id'))
    else:
        user.database.menu = User.Menu.ADMIN_MAIN
        change_user_status(user_id, ban_mode)
        user.send_message(user.translate('unbanned' if ban_mode is User.Status.ACTIVE else 'banned', user_id), admin)
