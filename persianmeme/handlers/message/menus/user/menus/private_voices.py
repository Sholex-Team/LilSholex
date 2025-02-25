from persianmeme.functions import make_string_keyboard_list
from persianmeme.keyboards import per_back
from persianmeme.models import User
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'افزودن ویس ⏬':
            if await user.private_voices_count <= 120:
                user.database.menu = User.Menu.USER_PRIVATE_VOICE_NAME
                user.database.back_menu = 'manage_private_voices'
                await user.send_message(
                    user.translate('meme_name', user.translate('voice')), per_back
                )
            else:
                await user.send_message(user.translate('voice_limit'))
        case 'مشاهده ی ویس ها 📝':
            voices, prev_page, next_page = await user.get_private_voices()
            if isinstance(voices, tuple):
                await user.send_message(
                    user.translate('empty_private_voices'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
                )
            else:
                await user.send_message(
                    *await make_string_keyboard_list(ObjectType.PRIVATE_VOICE, voices, prev_page, next_page)
                )
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
