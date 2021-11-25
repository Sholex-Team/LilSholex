from persianmeme.models import User
from persianmeme.classes import User as UserClass
from persianmeme.keyboards import admin


def handler(message_id: int, user: UserClass):
    user.database.menu = User.Menu.ADMIN_MAIN
    if user.edit_current_ad(message_id):
        user.send_message(user.translate('ad_edited'), admin)
    else:
        user.send_message(user.translate('ad_deleted'), admin)
