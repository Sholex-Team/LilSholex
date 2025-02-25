from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'حذف ویدئو ❌' | 'حذف ویس ❌':
            async with TaskGroup() as tg:
                if await user.delete_owned_meme():
                    tg.create_task(user.send_message(
                        user.translate('meme_deleted', user.current_meme_translation)
                    ))
                else:
                    tg.create_task(user.send_message(
                        user.translate('meme_is_not_yours', user.current_meme_translation)
                    ))
                tg.create_task(user.go_back())
        case 'تماشای ویدئو 👁' | 'گوش دادن به ویس 🎧':
            await user.send_current_meme()
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
