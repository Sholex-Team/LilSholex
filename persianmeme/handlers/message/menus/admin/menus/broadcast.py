from persianmeme.models import User
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.ADMIN_MAIN
    await user.send_message(user.translate(
        'broadcast_started', await user.broadcast(telegram_context.common.MESSAGE_ID.get())
    ), admin)
