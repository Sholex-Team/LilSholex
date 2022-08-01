from persianmeme.keyboards import user as user_keyboard, back as back_keyboard
from persianmeme.models import User
from persianmeme.classes import User as UserClass

def handler(text: str, user: UserClass):
    match text:
        case 'بله':
            user.database.menu = User.Menu.USER_TRIM_DURATION
            user.database.back_menu = User.Menu.USER_TRIM_VOICE_YES_OR_NO
            user.database.last_meme_file = user.download_file(user.get_file_path(user.database.last_meme.file_id))
            user.send_message(user.translate('send_duration', user.temp_meme_translation), back_keyboard)
        case 'خیر':
            user.database.menu = User.Menu.USER_MAIN
            user.database.last_meme.send_vote(user.session)
            user.send_message(user.translate('meme_added', user.temp_meme_translation), user_keyboard)