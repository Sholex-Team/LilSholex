from persianmeme.models import User
from persianmeme.classes import User as UserClass


def handler(text: str, user: UserClass):
    user.database.temp_meme_name = text
    user.database.menu = User.Menu.USER_PRIVATE_VOICE_TAGS
    user.database.back_menu = 'private_name'
    user.send_message(user.translate('send_meme_tags', user.translate('voice')))
