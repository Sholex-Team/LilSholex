from persianmeme.models import User, MemeType
from persianmeme.classes import User as UserClass
from persianmeme.translations import admin_messages
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    match telegram_context.message.TEXT.get():
        case 'Video':
            user.database.temp_meme_type = MemeType.VIDEO
        case 'Voice':
            user.database.temp_meme_type = MemeType.VOICE
        case 'Both':
            user.database.temp_meme_type = None
        case _:
            await user.send_message(
                admin_messages['unknown_command'], reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
            )
            return
    user.clear_current_meme()
    if await user.assign_meme():
        user.database.back_menu = 'meme_review_type'
        user.database.menu = User.Menu.ADMIN_MEME_REVIEW
