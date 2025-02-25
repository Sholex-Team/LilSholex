from persianmeme.models import MemeType, User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.USER_SUGGEST_MEME_TAGS
    user.database.temp_meme_name = telegram_context.message.TEXT.get()
    user.database.back_menu = 'suggest_voice_name' \
        if user.database.temp_meme_type == MemeType.VOICE \
        else 'suggest_video_name'
    await user.send_message(user.translate('send_meme_tags', user.temp_meme_translation))
