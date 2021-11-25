from persianmeme.models import Ad, User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import admin


def handler(message_id: int, user: UserClass):
    user.database.menu = User.Menu.ADMIN_MAIN
    ad_id = Ad.objects.create(chat_id=user.database.chat_id, message_id=message_id).ad_id
    user.send_message(
        user.translate('ad_submitted', ad_id), admin
    )
