from persianmeme.classes import User as UserClass
from persianmeme.functions import create_description
from persianmeme.translations import admin_messages
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    await user.edit_meme_tags()
    user.database.current_meme.description = create_description(user.database.current_meme.tags)
    await user.database.current_meme.asave(update_fields=('tags', 'description'))
    async with TaskGroup() as tg:
        tg.create_task(
            user.send_message(admin_messages['meme_tags_and_description_edited'].format(user.current_meme_translation))
        )
        tg.create_task(user.go_back())
