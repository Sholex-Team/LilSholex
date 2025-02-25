from persianmeme.models import User
from persianmeme.keyboards import settings
from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match text := telegram_context.message.TEXT.get():
        case 'روشن 🔛' | 'خاموش 🔴':
            user.database.back_menu = 'main'
            user.database.menu = User.Menu.USER_SETTINGS
            if text == 'روشن 🔛':
                user.database.use_recent_memes = True
                await user.send_message(user.translate('recent_memes_on'), settings)
            else:
                user.database.use_recent_memes = False
                async with TaskGroup() as tg:
                    tg.create_task(user.clear_recent_memes())
                    tg.create_task(user.send_message(user.translate('recent_memes_off'), settings))
        case _:
            await user.send_message(user.translate('unknown_command'))
