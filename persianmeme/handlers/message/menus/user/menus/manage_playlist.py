from persianmeme.models import User
from persianmeme.keyboards import per_back
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass
from persianmeme.functions import make_string_keyboard_list
from asyncio import TaskGroup
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.MESSAGE.get():
        case 'افزودن ویس ⏬':
            user.database.menu = User.Menu.USER_ADD_VOICE_PLAYLIST
            user.database.back_menu = 'manage_playlist'
            await user.send_message(user.translate('send_private_voice'), per_back)
        case 'حذف پلی لیست ❌':
            async with TaskGroup() as tg:
                tg.create_task(user.database.current_playlist.adelete())
                tg.create_task(user.send_message(
                    user.translate('playlist_deleted'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
                ))
                tg.create_task(user.go_back())
        case 'مشاهده ی ویس ها 📝':
            voices, prev_page, next_page = await user.get_playlist_voices()
            if isinstance(voices, tuple):
                await user.send_message(
                    user.translate('empty_playlist'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
                )
            else:
                await user.send_message(
                    *await make_string_keyboard_list(ObjectType.PLAYLIST_VOICE, voices, prev_page, next_page)
                )
        case 'لینک دعوت 🔗':
            await user.send_message(user.translate(
                'playlist_link',
                user.database.current_playlist.name,
                user.database.current_playlist.get_link()
            ))
        case 'مشترکین پلی لیست 👥':
            await user.send_message(user.translate(
                'playlist_users_count', await user.get_playlist_member_count()
            ))
        case _:
            await user.send_message(user.translate('unknown_command'))
