from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import voice_suggestions, manage_voice_list, manage_playlists


def handler(text: str, message_id: int, user: UserClass):
    matched = True
    match text:
        case 'ویس های پیشنهادی ✔':
            user.database.menu = User.Menu.USER_VOICE_SUGGESTIONS
            keyboard = voice_suggestions
        case 'ویس های شخصی 🔒':
            user.database.menu = User.Menu.USER_PRIVATE_VOICES
            keyboard = manage_voice_list
        case 'پلی لیست ها ▶️':
            user.database.menu = User.Menu.USER_PLAYLISTS
            keyboard = manage_playlists
        case _:
            matched = False
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
    if matched:
        user.database.back_menu = 'manage_voices'
        user.send_message(user.translate('choose'), keyboard)
