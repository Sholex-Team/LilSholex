from persianmeme.keyboards import admin
from persianmeme.models import Broadcast, User
from persianmeme.classes import User as UserClass
from LilSholex.context import telegram as telegram_context


async def handler():
    user: UserClass = telegram_context.common.USER.get()
    try:
        broadcast = await Broadcast.objects.aget(id=telegram_context.message.TEXT.get())
    except (Broadcast.DoesNotExist, ValueError):
        await user.send_message(
            user.translate('invalid_broadcast_id'),
            reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
        )
    else:
        user.database.menu = User.Menu.ADMIN_MAIN
        await user.send_message(user.translate(
            'broadcast_status',
            broadcast.id,
            '✅' if broadcast.sent else '❌',
            await User.objects.filter(last_broadcast=broadcast).acount()
        ), admin, telegram_context.common.MESSAGE_ID.get())
