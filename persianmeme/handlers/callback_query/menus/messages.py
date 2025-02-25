from persianmeme.models import User
from persianmeme.keyboards import en_back
from persianmeme.classes import User as UserClass
from persianmeme.functions import get_message
from persianmeme.translations import admin_messages
from LilSholex.exceptions import RequestInterruption
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context
from persianmeme import context as meme_context
from LilSholex.functions import answer_callback_query


async def handler():
    inliner: UserClass = telegram_context.common.USER.get()
    await inliner.delete_message()
    if not (target_message := await get_message()):
        await inliner.database.asave()
        raise RequestInterruption()
    user = UserClass(instance=target_message.sender)
    async with TaskGroup() as tg:
        tg.create_task(user.send_message(user.translate('checked_by_admin')))
        match meme_context.callback_query.COMMAND.get():
            case 'read':
                tg.create_task(answer_callback_query(admin_messages['read'], False))
            case 'ban' if user.database.rank == user.database.Rank.USER:
                user.database.status = user.database.Status.BANNED
                tg.create_task(answer_callback_query(
                    inliner.translate('banned', user.database.chat_id), True
                ))
                tg.create_task(user.database.asave())
            case 'reply':
                inliner.database.menu = User.Menu.ADMIN_MESSAGE_USER
                inliner.database.menu_mode = inliner.database.MenuMode.ADMIN
                inliner.menu_cleanup()
                inliner.database.back_menu = 'chat_id'
                inliner.database.temp_user_id = user.database.chat_id
                tg.create_task(inliner.send_message(admin_messages['reply'], en_back))
                tg.create_task(answer_callback_query(admin_messages['replying'], False))
