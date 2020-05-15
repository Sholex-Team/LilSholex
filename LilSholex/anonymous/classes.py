from anonymous import models
import faster_than_requests as fast_req
from urllib.parse import urlencode
from django.conf import settings
from groupguard.decorators import fix
import json


class User:
    def __init__(self, chat_id: int = None, token: str = None, instance: models.User = None):
        if chat_id:
            self.database, created = models.User.objects.get_or_create(chat_id=chat_id)
        elif token:
            self.database = models.User.objects.get(token=token)
        else:
            assert instance, 'You must provide instance if there is not a chat_id !'
            self.database = instance

    @fix
    def send_message(
            self, text: str,
            /,
            reply_markup: dict = '',
            reply_to_message_id: int = '',
            parse_mode: str = '',
            disable_web_page_preview: bool = True
    ) -> int:

        if reply_markup != '':
            reply_markup = json.dumps(reply_markup)
        encoded = urlencode({'text': text, 'reply_markup': reply_markup})
        if (result := json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.ANONYMOUS}/sendMessage?chat_id={self.database.chat_id}&{encoded}&'
            f'reply_to_message_id={reply_to_message_id}&parse_mode={parse_mode}&'
            f'disable_web_page_preview={disable_web_page_preview}'
        )['body']))['ok']:
            return result['result']['message_id']
        return 0

    def send_url(self, telegram=True):
        if telegram:
            self.send_message(f'لینک شما: \n\nhttp://t.me/AnonymousSholexBot?start={self.database.token}')
