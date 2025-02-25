from persianmeme.translations import admin_messages
from persianmeme.models import User, MemeType
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.ADMIN_NEW_MEME
    if user.database.temp_meme_type == MemeType.VOICE:
        user.database.back_menu = 'voice_tags'
        meme_translation = admin_messages['voice']
    else:
        user.database.back_menu = 'video_tags'
        meme_translation = admin_messages['video']
    await user.send_message(user.translate('send_meme', meme_translation))
