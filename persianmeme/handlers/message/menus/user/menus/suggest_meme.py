from persianmeme.keyboards import user as user_keyboard
from persianmeme.models import User, Meme
from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    target_meme: Meme = meme_context.common.MEME.get()
    user.database.menu = User.Menu.USER_MAIN
    async with TaskGroup() as tg:
        tg.create_task(target_meme.send_vote())
        tg.create_task(
            user.send_message(user.translate('meme_added', user.temp_meme_translation), user_keyboard)
        )
    await target_meme.asave(update_fields=('task_id',))
