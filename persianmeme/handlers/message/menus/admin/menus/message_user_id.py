from persianmeme.models import User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    try:
        user.database.temp_user_id = int(telegram_context.message.TEXT.get())
    except (ValueError, TypeError):
        await user.send_message(user.translate('invalid_user_id'))
    else:
        user.database.menu = User.Menu.ADMIN_MESSAGE_USER
        user.database.back_menu = 'chat_id'
        await user.send_message(user.translate('message'))
