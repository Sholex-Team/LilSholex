from persianmeme.models import User
from persianmeme.classes import User as UserClass


def handler(user: UserClass):
    user.database.menu = User.Menu.USER_PRIVATE_VOICE
    user.database.back_menu = 'private_voice_tags'
    user.send_message(user.translate('send_meme', user.translate('voice')))
