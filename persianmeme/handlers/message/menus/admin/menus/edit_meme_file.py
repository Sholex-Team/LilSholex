from persianmeme.classes import User as UserClass
from persianmeme.translations import admin_messages
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if await user.edit_meme_file():
        async with TaskGroup() as tg:
            tg.create_task(user.send_message(admin_messages['meme_file_edited'].format(user.current_meme_translation)))
            tg.create_task(user.go_back())
