from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme import keyboards


def handler(message_id: int, user: UserClass):
    user.database.menu = User.Menu.ADMIN_MAIN
    user.copy_message(message_id, keyboards.admin_message, chat_id=user.database.temp_user_id)
    user.send_message(user.translate('sent'), keyboards.admin)
