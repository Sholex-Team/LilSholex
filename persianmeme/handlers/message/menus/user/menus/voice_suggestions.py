from persianmeme.functions import make_list_string
from persianmeme.keyboards import make_list
from persianmeme.models import MemeType
from persianmeme.types import ObjectType
from persianmeme.classes import User


def handler(text: str, message_id: int, user: User):
    match text:
        case 'پیشنهاد ویس 🔥':
            user.suggest_meme(MemeType.VOICE)
        case 'لغو رای گیری ⏹':
            user.cancel_voting(MemeType.VOICE)
        case 'مشاهده ی ویس ها 📝':
            voices, prev_page, next_page = user.get_suggestions(1, MemeType.VOICE)
            if voices:
                user.send_message(
                    make_list_string(ObjectType.SUGGESTED_VOICE, voices),
                    make_list(
                        ObjectType.SUGGESTED_VOICE, voices, prev_page, next_page
                    )
                )
            else:
                user.send_message(user.translate(
                    'empty_suggested_memes', user.translate('voice')
                ), reply_to_message_id=message_id)
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
