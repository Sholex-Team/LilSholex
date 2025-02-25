from persianmeme.models import User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.temp_meme_name = telegram_context.message.TEXT.get()
    user.database.menu = User.Menu.USER_PRIVATE_VOICE_TAGS
    user.database.back_menu = 'private_name'
    await user.send_message(user.translate('send_meme_tags', user.translate('voice')))
