from persianmeme.keyboards import admin
from persianmeme.models import User
from persianmeme.classes import User as UserClass
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler(ban_mode: User.Status):
    user: UserClass = telegram_context.common.USER.get()
    try:
        user_id = int(telegram_context.message.TEXT.get())
    except (ValueError, TypeError):
        await user.send_message(user.translate('invalid_user_id'))
    else:
        user.database.menu = User.Menu.ADMIN_MAIN
        async with TaskGroup() as tg:
            tg.create_task(User.objects.filter(chat_id=user_id).aupdate(status=ban_mode))
            tg.create_task(user.send_message(
                user.translate('unbanned' if ban_mode is User.Status.ACTIVE else 'banned', user_id),
                admin
            ))
