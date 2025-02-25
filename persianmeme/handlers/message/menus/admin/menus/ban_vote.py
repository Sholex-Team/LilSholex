from persianmeme.models import User, Meme
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context


async def handler():
    target_vote: Meme = meme_context.common.MEME.get()
    target_vote.sender.status = target_vote.sender.Status.BANNED
    user: UserClass = telegram_context.common.USER.get()
    user.database.menu = User.Menu.ADMIN_MAIN
    async with TaskGroup() as tg:
        tg.create_task(target_vote.sender.asave(update_fields=('status',)))
        tg.create_task(target_vote.deny())
        tg.create_task(user.send_message(user.translate('ban_voted'), admin))
