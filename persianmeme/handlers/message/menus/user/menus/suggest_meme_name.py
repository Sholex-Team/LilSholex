from persianmeme.models import MemeType, User
from persianmeme.classes import User as UserClass


def handler(text: str, user: UserClass):
    user.database.menu = User.Menu.USER_SUGGEST_MEME_TAGS
    user.database.temp_meme_name = text
    user.database.back_menu = 'suggest_voice_name' \
        if user.database.temp_meme_type == MemeType.VOICE \
        else 'suggest_video_name'
    user.send_message(user.translate('send_meme_tags', user.temp_meme_translation))
