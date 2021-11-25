from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import manage_voice_list


def handler(user: UserClass):
    user.database.menu = User.Menu.USER_PRIVATE_VOICES
    user.database.back_menu = 'manage_voices'
    user.send_message(user.translate('private_voice_added'), manage_voice_list)
