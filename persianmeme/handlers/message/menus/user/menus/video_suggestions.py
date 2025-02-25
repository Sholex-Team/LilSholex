from persianmeme.functions import make_string_keyboard_list
from persianmeme.models import MemeType
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'پیشنهاد ویدئو 🔥':
            await user.suggest_meme(MemeType.VIDEO)
        case 'لغو رای گیری ⏹':
            await user.cancel_voting(MemeType.VIDEO)
        case 'مشاهده ی ویدئو ها 📝':
            videos, prev_page, next_page = await user.get_suggestions(MemeType.VIDEO)
            if isinstance(videos, tuple):
                await user.send_message(user.translate(
                    'empty_suggested_memes', user.translate('video')
                ), reply_to_message_id=telegram_context.common.MESSAGE_ID.get())
            else:
                await user.send_message(
                    *await make_string_keyboard_list(ObjectType.SUGGESTED_VIDEO, videos, prev_page, next_page)
                )
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
