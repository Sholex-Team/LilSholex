from json import loads
from persianmeme.classes import User
from django.conf import settings


def handler(text: str, message_id: int, user: User):
    help_messages = loads(settings.MEME_HELP_MESSAGES)
    if text in help_messages:
        user.send_animation(**help_messages[text], reply_to_message_id=message_id)
    else:
        user.send_message(user.translate('unknown_command'), reply_to_message_id=message_id)
