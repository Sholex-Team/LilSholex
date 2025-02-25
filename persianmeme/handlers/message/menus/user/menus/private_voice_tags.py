from persianmeme.models import User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.USER_PRIVATE_VOICE
    user.database.back_menu = 'private_voice_tags'
    await user.send_message(user.translate('send_meme', user.translate('voice')))
