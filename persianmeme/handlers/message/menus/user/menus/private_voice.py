from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import manage_voice_list
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.USER_PRIVATE_VOICES
    user.database.back_menu = 'manage_voices'
    await user.send_message(user.translate('private_voice_added'), manage_voice_list)
