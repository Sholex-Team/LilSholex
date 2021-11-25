from persianmeme.models import User
from persianmeme.keyboards import en_back
from persianmeme.classes import User as UserClass
from persianmeme.functions import get_message
from persianmeme.translations import admin_messages
from LilSholex.exceptions import RequestInterruption


def handler(command: str, target_id: int, message_id: int, query_id: str, answer_query, inliner: UserClass):
    inliner.delete_message(message_id)
    if not (target_message := get_message(target_id)):
        inliner.database.save()
        raise RequestInterruption()
    user = UserClass(
        inliner.session, UserClass.Mode.NORMAL, instance=target_message.sender
    )
    user.send_message(user.translate('checked_by_admin'))
    match command:
        case 'read':
            answer_query(query_id, admin_messages['read'], False)
        case 'ban' if user.database.rank == user.database.Rank.USER:
            user.database.status = user.database.Status.BANNED
            answer_query(query_id, inliner.translate('banned', user.database.chat_id), True)
            user.database.save()
        case 'reply':
            inliner.database.menu = User.Menu.ADMIN_MESSAGE_USER
            inliner.database.menu_mode = inliner.database.MenuMode.ADMIN
            inliner.menu_cleanup()
            inliner.database.back_menu = 'chat_id'
            inliner.database.temp_user_id = user.database.chat_id
            inliner.send_message(admin_messages['reply'], en_back)
            answer_query(query_id, admin_messages['replying'], False)
