from persianmeme.models import Meme, User
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass


def handler(message: dict, user: UserClass):
    if user.add_meme(message, Meme.Status.ACTIVE):
        user.database.menu = User.Menu.ADMIN_MAIN
        user.send_message(
            user.translate('meme_added', user.temp_meme_translation), admin
        )
