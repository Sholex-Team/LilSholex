from persianmeme.models import MemeType
from persianmeme.classes import User


def handler(text: str, message_id: int, user: User):
    match text:
        case 'ویس 🔊':
            user.suggest_meme(MemeType.VOICE)
        case 'ویدئو 📹':
            user.suggest_meme(MemeType.VIDEO)
        case _:
            user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
