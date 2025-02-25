from persianmeme.models import User
from persianmeme.keyboards import user as user_keyboard
from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.USER_MAIN
    async with TaskGroup() as tg:
        tg.create_task(user.contact_admin())
        tg.create_task(user.send_message(
            user.translate('message_sent'), user_keyboard, telegram_context.common.MESSAGE_ID.get()
        ))
