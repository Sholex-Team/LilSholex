from persianmeme.models import Meme, User
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if await user.add_meme(Meme.Status.ACTIVE):
        user.database.menu = User.Menu.ADMIN_MAIN
        await user.send_message(
            user.translate('meme_added', user.temp_meme_translation), admin
        )
