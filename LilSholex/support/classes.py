import faster_than_requests as fast_req
import json
from urllib.parse import urlencode
from support import models, keyboards
from support.translators import commands
from django.conf import settings


class User:
    def __init__(self, chat_id: int = None, /, *, instance: models.User = None):
        if not chat_id:
            assert instance, 'Instance must be passes when chat id isn\'t !'
            self.database = instance
        else:
            self.database, created = models.User.objects.get_or_create(chat_id=chat_id)

    def send_message(self, text: str, reply_markup: dict = '', /, reply_to_message_id: int = ''):
        if reply_markup:
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'text': text, 'reply_markup': reply_markup})
        fast_req.get(
            f'https://api.telegram.org/bot{settings.SUPPORT}/sendMessage?{encoded}&chat_id={self.database.chat_id}&'
            f'reply_to_message_id={reply_to_message_id}'
        )

    def edit_message_reply_markup(self, message_id: int, reply_markup: dict):
        encoded = urlencode({'reply_markup': json.dumps(reply_markup)})
        fast_req.get(
            f'https://api.telegram.org/bot{settings.SUPPORT}/editMessageReplyMarkup?chat_id={self.database.chat_id}&'
            f'message_id={message_id}&{encoded}'
        )

    def get_keyboard(self, keyboard):
        return getattr(keyboards, f'{self.database.lang}_{keyboard}')

    def translate(self, cmd, *args):
        return commands[cmd][self.database.lang].format(*args)


def answer_callback_query(callback_query_id: str, text: str, show_alert: bool = False, /):
    encoded = urlencode({'text': text})
    fast_req.get(
        f'https://api.telegram.org/bot{settings.SUPPORT}/answerCallbackQuery?callback_query_id={callback_query_id}&'
        f'{encoded}&show_alert={show_alert}'
    )
