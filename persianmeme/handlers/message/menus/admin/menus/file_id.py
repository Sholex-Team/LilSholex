from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import admin
from LilSholex.context import telegram as telegram_context


async def handler():
    message: dict = telegram_context.message.MESSAGE.get()
    user: UserClass = telegram_context.common.USER.get()
    if document := message.get('document') or message.get('video'):
        user.database.menu = User.Menu.ADMIN_MAIN
        await user.send_message(
            user.translate('file_id', document['file_id'], document['file_unique_id']),
            admin,
            telegram_context.common.MESSAGE_ID.get(),
            'HTML'
        )
    else:
        await user.send_message(
            user.translate('no_document'), reply_to_message_id=telegram_context.common.MESSAGE_ID.get()
        )
