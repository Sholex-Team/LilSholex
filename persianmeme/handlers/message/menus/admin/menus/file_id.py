from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import admin


def handler(message: dict, message_id: int, user: UserClass):
    if message.get('document'):
        user.database.menu = User.Menu.ADMIN_MAIN
        user.send_message(
            user.translate('file_id', message['document']['file_id']),
            admin,
            message_id
        )
    else:
        user.send_message(user.translate('no_document'), reply_to_message_id=message_id)
