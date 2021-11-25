from persianmeme.models import User, Meme
from persianmeme.keyboards import edit_meme
from persianmeme.classes import User as UserClass


def handler(target_meme: Meme, user: UserClass):
    user.database.current_meme = target_meme
    user.database.back_menu = 'send_edit_meme'
    user.database.menu = User.Menu.ADMIN_EDIT_MEME
    user.send_message(user.translate('edit_meme', user.current_meme_translation), edit_meme)
