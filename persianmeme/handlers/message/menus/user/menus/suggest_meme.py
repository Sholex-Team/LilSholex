from persianmeme.keyboards import user as user_keyboard
from persianmeme.models import User, Meme
from persianmeme.classes import User as UserClass


def handler(target_meme: Meme, user: UserClass):
    user.database.menu = User.Menu.USER_MAIN
    target_meme.send_vote(user.session)
    user.send_message(user.translate('meme_added', user.temp_meme_translation), user_keyboard)
