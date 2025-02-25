from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if (text := telegram_context.message.TEXT.get()) and len(text) <= 60:
        async with TaskGroup() as tg:
            tg.create_task(user.send_message(
                user.translate('playlist_created', (await user.create_playlist()).get_link())
            ))
            tg.create_task(user.go_back())
    else:
        await user.send_message(
            user.translate('invalid_playlist_name'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
        )
