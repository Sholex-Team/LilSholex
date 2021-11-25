from persianmeme.models import User, Ad
from persianmeme.keyboards import admin
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    try:
        Ad.objects.get(ad_id=int(text)).delete()
    except (ValueError, Ad.DoesNotExist):
        user.send_message(
            user.translate('invalid_ad_id'), reply_to_message_id=message_id
        )
    else:
        user.database.menu = User.Menu.ADMIN_MAIN
        user.send_message(user.translate('ad_deleted'), admin)
