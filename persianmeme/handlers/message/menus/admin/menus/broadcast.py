from persianmeme.models import User
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass


def handler(message_id: int, user: UserClass):
    user.database.menu = User.Menu.ADMIN_MAIN
    user.send_message(
        user.translate('broadcast_started', user.broadcast(message_id)), admin
    )
