from persianmeme.models import User, Meme
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import admin


def handler(target_meme: Meme, user: UserClass):
    target_meme.accept(user.session)
    target_meme.delete_vote(user.session)
    user.database.menu = User.Menu.ADMIN_MAIN
    user.send_message(user.translate('admin_meme_accepted', user.translate(target_meme.type_string)), admin)
