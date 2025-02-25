from persianmeme.keyboards import admin
from persianmeme.models import User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if (text := telegram_context.message.TEXT.get()) and text.isdecimal():
        user.database.menu = User.Menu.ADMIN_MAIN
        await user.send_message(
            user.translate('user_profile', text),
            admin,
            telegram_context.common.MESSAGE_ID.get(),
            'Markdown'
        )
    else:
        await user.send_message(user.translate('invalid_user_id'))