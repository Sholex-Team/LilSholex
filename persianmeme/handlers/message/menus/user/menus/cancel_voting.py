from persianmeme.classes import User as UserClass
from persianmeme.translations import user_messages
from persianmeme.models import MemeType
from LilSholex.context import telegram as telegram_context

async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'ویس 🔊':
            await user.cancel_voting(MemeType.VOICE)
        case 'ویدئو 📹':
            await user.cancel_voting(MemeType.VIDEO)
        case _:
            await user.send_message(user_messages['unknown_command'])
            return
    await user.go_back()
