from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import voice_suggestions, manage_voice_list, manage_playlists
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    matched = True
    match telegram_context.message.TEXT.get():
        case 'ویس های پیشنهادی ✔':
            user.database.menu = User.Menu.USER_VOICE_SUGGESTIONS
            keyboard = voice_suggestions
        case 'ویس های شخصی 🔒':
            user.database.menu = User.Menu.USER_PRIVATE_VOICES
            keyboard = manage_voice_list
        case 'پلی لیست ها ▶️':
            user.database.menu = User.Menu.USER_PLAYLISTS
            keyboard = manage_playlists
        case _:
            matched = False
            await user.send_message(
                user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
    if matched:
        user.database.back_menu = 'manage_voices'
        await user.send_message(user.translate('choose'), keyboard)
