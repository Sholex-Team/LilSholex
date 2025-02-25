from persianmeme.models import MemeType
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'ویس 🔊':
            await user.suggest_meme(MemeType.VOICE)
        case 'ویدئو 📹':
            await user.suggest_meme(MemeType.VIDEO)
        case _:
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
