from persianmeme.functions import make_list_string
from persianmeme.keyboards import per_back, make_list
from persianmeme.models import User
from persianmeme.types import ObjectType
from persianmeme.classes import User as UserClass


def handler(text: str, message_id: int, user: UserClass):
    match text:
        case 'افزودن ویس ⏬':
            if user.private_voices_count <= 120:
                user.database.menu = User.Menu.USER_PRIVATE_VOICE_NAME
                user.database.back_menu = 'manage_private_voices'
                user.send_message(
                    user.translate('meme_name', user.translate('voice')), per_back
                )
            else:
                user.send_message(user.translate('voice_limit'))
        case 'مشاهده ی ویس ها 📝':
            voices, prev_page, next_page = user.get_private_voices(1)
            if voices:
                user.send_message(
                    make_list_string(ObjectType.PRIVATE_VOICE, voices),
                    make_list(ObjectType.PRIVATE_VOICE, voices, prev_page, next_page)
                )
            else:
                user.send_message(
                    user.translate('empty_private_voices'), reply_to_message_id=message_id
                )
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
