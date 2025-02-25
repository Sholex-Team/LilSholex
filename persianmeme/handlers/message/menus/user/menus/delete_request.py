from persianmeme import classes
from persianmeme.classes import User as UserClass
from persianmeme.models import User
from persianmeme.translations import admin_messages
from persianmeme.keyboards import user as user_keyboard
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    owner = classes.User(instance=await User.objects.filter(rank='o').afirst())
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.USER_MAIN
    async with TaskGroup() as tg:
        tg.create_task(user.send_message(
            user.translate('request_created'), user_keyboard, telegram_context.common.MESSAGE_ID.get()
        ))
        tg.create_task(user.delete_request())
        tg.create_task(owner.send_message(admin_messages['new_delete_request']))
