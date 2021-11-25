from persianmeme.models import User
from persianmeme.functions import make_list_string
from persianmeme.keyboards import per_back, make_list
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    match text:
        case 'افزودن ویس ⏬':
            user.database.menu = User.Menu.USER_ADD_VOICE_PLAYLIST
            user.database.back_menu = 'manage_playlist'
            user.send_message(user.translate('send_private_voice'), per_back)
        case 'حذف پلی لیست ❌':
            user.delete_playlist()
            user.send_message(
                user.translate('playlist_deleted'), reply_to_message_id=message_id
            )
            user.go_back()
        case 'مشاهده ی ویس ها 📝':
            voices, prev_page, next_page = user.get_playlist_voices(1)
            if voices:
                user.send_message(
                    make_list_string(ObjectType.PLAYLIST_VOICE, voices),
                    make_list(ObjectType.PLAYLIST_VOICE, voices, prev_page, next_page)
                )
            else:
                user.send_message(
                    user.translate('empty_playlist'), reply_to_message_id=message_id
                )
        case 'لینک دعوت 🔗':
            user.send_message(user.translate(
                'playlist_link',
                user.database.current_playlist.name,
                user.database.current_playlist.get_link()
            ))
        case 'مشترکین پلی لیست 👥':
            user.send_message(user.translate(
                'playlist_users_count', user.database.current_playlist.user_playlist.count()
            ))
        case _:
            user.send_message(user.translate('unknown_command'))
