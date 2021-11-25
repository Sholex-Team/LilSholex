from persianmeme.keyboards import settings
from persianmeme.models import User
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    match text:
        case 'روشن 🔛' | 'خاموش 🔴':
            user.database.back_menu = 'main'
            user.database.menu = User.Menu.USER_SETTINGS
            if text == 'روشن 🔛':
                user.database.vote = True
                user.send_message(user.translate('voting_on'), settings)
            else:
                user.database.vote = False
                user.send_message(user.translate('voting_off'), settings)
        case _:
            user.send_message(
                user.translate('unknown_command'), reply_to_message_id=message_id
            )
