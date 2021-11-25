from persianmeme.models import MemeType, User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import en_back


def handler(text: str, user: UserClass):
    matched = True
    match text:
        case "Video":
            user.database.temp_meme_type = MemeType.VIDEO
            meme_translation = user.translate('video')
        case "Voice":
            user.database.temp_meme_type = MemeType.VOICE
            meme_translation = user.translate('voice')
        case _:
            matched = False
    if matched:
        user.database.back_menu = 'meme_type'
        user.database.menu = User.Menu.ADMIN_MEME_NAME
        user.send_message(user.translate('meme_name', meme_translation), en_back)
