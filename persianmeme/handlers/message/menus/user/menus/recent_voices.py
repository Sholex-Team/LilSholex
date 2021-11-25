from persianmeme.models import User
from persianmeme.keyboards import settings
from persianmeme.classes import User as UserClass


def handler(text: str, user: UserClass):
    match text:
        case 'روشن 🔛' | 'خاموش 🔴':
            user.database.back_menu = 'main'
            user.database.menu = User.Menu.USER_SETTINGS
            if text == 'روشن 🔛':
                user.database.use_recent_memes = True
                user.send_message(user.translate('recent_memes_on'), settings)
            else:
                user.database.use_recent_memes = False
                user.clear_recent_memes()
                user.send_message(user.translate('recent_memes_off'), settings)
        case _:
            user.send_message(user.translate('unknown_command'))
