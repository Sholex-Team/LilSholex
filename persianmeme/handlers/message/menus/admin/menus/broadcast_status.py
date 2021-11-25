from persianmeme.keyboards import admin
from persianmeme.models import Broadcast, User
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    try:
        broadcast = Broadcast.objects.get(id=text)
    except (Broadcast.DoesNotExist, ValueError):
        user.send_message(
            user.translate('invalid_broadcast_id'), reply_to_message_id=message_id
        )
    else:
        user.database.menu = User.Menu.ADMIN_MAIN
        user.send_message(user.translate(
            'broadcast_status',
            broadcast.id,
            '✅' if broadcast.sent else '❌',
            User.objects.filter(last_broadcast=broadcast).count()
        ), admin, message_id)
