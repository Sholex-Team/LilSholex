from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'حذف ویس ❌':
            async with TaskGroup() as tg:
                if await user.remove_voice_from_playlist():
                    tg.create_task(user.send_message(user.translate('deleted_from_playlist')))
                else:
                    tg.create_task(user.send_message(user.translate('not_in_playlist')))
                tg.create_task(user.go_back())
        case 'گوش دادن به ویس 🎧':
            await user.send_current_meme()
        case _:
            await user.send_message(user.translate('unknown_command'))
