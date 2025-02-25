from persianmeme.keyboards import settings
from persianmeme.models import User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match text := telegram_context.message.TEXT.get():
        case 'روشن 🔛' | 'خاموش 🔴':
            user.database.back_menu = 'main'
            user.database.menu = User.Menu.USER_SETTINGS
            if text == 'روشن 🔛':
                user.database.vote = True
                await user.send_message(user.translate('voting_on'), settings)
            else:
                user.database.vote = False
                await user.send_message(user.translate('voting_off'), settings)
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
