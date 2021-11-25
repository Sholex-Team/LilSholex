from persianmeme.models import User, Ad
from persianmeme.keyboards import en_back
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    try:
        user.database.current_ad = Ad.objects.get(ad_id=text)
    except (Ad.DoesNotExist, ValueError):
        user.send_message(
            user.translate('invalid_ad_id'), reply_to_message_id=message_id
        )
    else:
        user.database.back_menu = 'edit_ad'
        user.database.menu = User.Menu.ADMIN_EDIT_AD
        user.send_message(user.translate('replace_ad'), en_back)
