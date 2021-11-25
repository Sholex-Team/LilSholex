from persianmeme import classes
from persianmeme.classes import User as UserClass
from persianmeme.models import User, Meme
from persianmeme.translations import admin_messages
from persianmeme.keyboards import user as user_keyboard


def handler(message_id: int, target_meme: Meme, user: UserClass):
    owner = classes.User(
        user.session,
        classes.User.Mode.NORMAL,
        instance=User.objects.filter(rank='o').first()
    )
    user.database.menu = User.Menu.USER_MAIN
    user.send_message(
        user.translate('request_created'), user_keyboard, message_id
    )
    user.delete_request(target_meme)
    owner.send_message(admin_messages['new_delete_request'])
