from persianmeme.models import MemeType, User
from persianmeme.translations import admin_messages
from persianmeme.classes import User as UserClass


def handler(message: dict, text: str, user: UserClass):
    if user.validate_meme_name(message, text, user.database.temp_meme_type):
        user.database.menu = User.Menu.ADMIN_MEME_TAGS
        user.database.temp_meme_name = text
        if user.database.temp_meme_type == MemeType.VOICE:
            user.database.back_menu = 'voice_name'
            meme_translation = admin_messages['voice']
        else:
            user.database.back_menu = 'video_name'
            meme_translation = admin_messages['video']
        user.send_message(user.translate('send_meme_tags', meme_translation))