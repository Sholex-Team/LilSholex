from persianmeme.models import User, Meme
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass


def handler(target_meme: Meme, user: UserClass):
    target_meme.delete_vote(user.session)
    target_meme.deny(user.session)
    user.database.menu = User.Menu.ADMIN_MAIN
    user.send_message(user.translate('admin_meme_denied', user.translate(target_meme.type_string)), admin)
