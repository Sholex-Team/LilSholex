from persianmeme.functions import make_list_string
from persianmeme.keyboards import per_back, make_list
from persianmeme.models import User
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    match text:
        case 'ایجاد پلی لیست 🆕':
            user.database.back_menu = 'manage_playlists'
            user.database.menu = User.Menu.USER_CREATE_PLAYLIST
            user.send_message(user.translate('playlist_name'), per_back)
        case 'مشاهده پلی لیست ها 📝':
            current_page, prev_page, next_page = user.get_playlists(1)
            if current_page:
                user.send_message(
                    make_list_string(ObjectType.PLAYLIST, current_page),
                    make_list(
                        ObjectType.PLAYLIST, current_page, prev_page, next_page
                    )
                )
            else:
                user.send_message(
                    user.translate('no_playlist'), reply_to_message_id=message_id
                )
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
