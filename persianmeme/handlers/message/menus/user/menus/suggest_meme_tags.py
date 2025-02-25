from persianmeme.models import User, MemeType
from persianmeme.classes import User as UserClass
from persianmeme.translations import user_messages
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.USER_SUGGEST_MEME
    if user.database.temp_meme_type == MemeType.VOICE:
        user.database.back_menu = 'suggest_voice_tags'
        await user.send_message(user_messages['send_meme'].format(user.temp_meme_translation))
    else:
        user.database.back_menu = 'suggest_video_tags'
        await user.send_message(user_messages['send_a_video'])
