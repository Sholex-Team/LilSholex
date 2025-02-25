from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if await user.add_voice_to_playlist():
        async with TaskGroup() as tg:
            tg.create_task(user.send_message(user.translate('added_to_playlist')))
            tg.create_task(user.go_back())
    else:
        await user.send_message(
            user.translate('meme_is_not_yours', user.translate('voice')),
            reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
        )
