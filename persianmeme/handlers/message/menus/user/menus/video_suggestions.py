from persianmeme.functions import make_list_string
from persianmeme.keyboards import make_list
from persianmeme.models import MemeType
from persianmeme.types import ObjectType
from persianmeme.classes import User


def handler(text: str, message_id: int, user: User):
    match text:
        case 'پیشنهاد ویدئو 🔥':
            user.suggest_meme(MemeType.VIDEO)
        case 'لغو رای گیری ⏹':
            user.cancel_voting(MemeType.VIDEO)
        case 'مشاهده ی ویدئو ها 📝':
            videos, prev_page, next_page = user.get_suggestions(1, MemeType.VIDEO)
            if videos:
                user.send_message(
                    make_list_string(ObjectType.SUGGESTED_VIDEO, videos),
                    make_list(
                        ObjectType.SUGGESTED_VIDEO, videos, prev_page, next_page
                    )
                )
            else:
                user.send_message(user.translate(
                    'empty_suggested_memes', user.translate('video')
                ), reply_to_message_id=message_id)
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
