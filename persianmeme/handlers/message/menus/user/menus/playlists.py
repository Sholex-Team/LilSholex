from persianmeme.functions import make_string_keyboard_list
from persianmeme.keyboards import per_back
from persianmeme.models import User
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'ایجاد پلی لیست 🆕':
            user.database.back_menu = 'manage_playlists'
            user.database.menu = User.Menu.USER_CREATE_PLAYLIST
            await user.send_message(user.translate('playlist_name'), per_back)
        case 'مشاهده پلی لیست ها 📝':
            current_page, prev_page, next_page = await user.get_playlists()
            if isinstance(current_page, tuple):
                await user.send_message(
                    user.translate('no_playlist'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
                )
            else:
                await user.send_message(
                    *await make_string_keyboard_list(ObjectType.PLAYLIST, current_page, prev_page, next_page)
                )
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
