from persianmeme.classes import User as UserClass
from django.conf import settings
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    if meme_help_message := settings.MEME_HELP_MESSAGES.get(telegram_context.message.TEXT.get()):
        await user.send_animation(**meme_help_message, reply_to_message_id=telegram_context.common.MESSAGE_ID.get())
    else:
        await user.send_message(
            user.translate('unknown_command'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
        )
