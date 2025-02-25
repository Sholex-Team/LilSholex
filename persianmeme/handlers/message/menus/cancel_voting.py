from persianmeme.classes import User as UserClass
from persianmeme.models import MemeType
from persianmeme.translations import user_messages
from persianmeme.models import User
from persianmeme.keyboards import per_meme_type
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get().split(maxsplit=1):
        case ('/cancelvoting', 'VOICE'):
            await user.cancel_voting(MemeType.VOICE)
        case ('/cancelvoting', 'VIDEO'):
            await user.cancel_voting(MemeType.VIDEO)
        case ('/cancelvoting',):
            user.menu_cleanup()
            user.database.back_menu = 'main'
            user.database.menu_mode = User.MenuMode.USER
            user.database.menu = User.Menu.USER_CANCEL_VOTING
            await user.send_message(user_messages['meme_type'], per_meme_type, telegram_context.common.MESSAGE_ID.get())
        case _:
            await user.send_message(user_messages['unknown_command'])
