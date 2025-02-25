from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme import keyboards
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.ADMIN_MAIN
    async with TaskGroup() as tg:
        tg.create_task(user.copy_message(
            telegram_context.common.MESSAGE_ID.get(),
            keyboards.admin_message,
            chat_id=user.database.temp_user_id,
            protect_content=True
        ))
        tg.create_task(user.send_message(user.translate('sent'), keyboards.admin))
