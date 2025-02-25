from persianmeme.models import MemeType, User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import en_back
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'Video':
            user.database.temp_meme_type = MemeType.VIDEO
            meme_translation = user.translate('video')
        case 'Voice':
            user.database.temp_meme_type = MemeType.VOICE
            meme_translation = user.translate('voice')
        case _:
            return
    user.database.back_menu = 'meme_type'
    user.database.menu = User.Menu.ADMIN_MEME_NAME
    await user.send_message(user.translate('meme_name', meme_translation), en_back)
