from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    await user.edit_meme_tags()
    await user.database.current_meme.asave(update_fields=('tags',))
    async with TaskGroup() as tg:
        tg.create_task(
            user.send_message(user.translate('meme_tags_edited', user.current_meme_translation))
        )
        tg.create_task(user.go_back())
