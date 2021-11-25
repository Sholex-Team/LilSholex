from persianmeme.models import User
from persianmeme.keyboards import user as user_keyboard
from persianmeme.classes import User as UserClass


def handler(message_id: int, user: UserClass):
    user.database.menu = User.Menu.USER_MAIN
    user.contact_admin(message_id)
    user.send_message(user.translate('message_sent'), user_keyboard, message_id)
