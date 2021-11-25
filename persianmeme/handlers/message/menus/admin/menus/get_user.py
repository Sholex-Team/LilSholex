from persianmeme.keyboards import admin
from persianmeme.models import User


def handler(text, user, message_id):
    if text:
        try:
            int(text)
        except ValueError:
            user.send_message(
                user.translate('invalid_user_id'), reply_to_message_id=message_id
            )
        else:
            user.database.menu = User.Menu.ADMIN_MAIN
            user.send_message(
                user.translate('user_profile', text),
                admin,
                message_id,
                'Markdown'
            )
    else:
        user.send_message(user.translate('invalid_user_id'))