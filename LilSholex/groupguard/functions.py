import faster_than_requests as fast_req
import json
from django.conf import settings
from groupguard.decorators import fix
from urllib.parse import urlencode
import datetime


@fix
def get_chat_member(chat_id, user_id: int):
    if (result := json.loads(fast_req.get(
        f'https://api.telegram.org/bot{settings.GROUP}/getChatMember?chat_id={chat_id}&user_id={user_id}'
    )['body']))['ok']:
        return result['result']


def delete_message(chat_id: int, message_id: int, /) -> None:
    fast_req.get(
        f'https://api.telegram.org/bot{settings.GROUP}/deleteMessage?chat_id={chat_id}&message_id={message_id}'
    )


def answer_callback_query(callback_query_id: str, text: str, show_alert: bool = False, /):
    encoded = urlencode({'text': text})
    fast_req.get(
        f'https://api.telegram.org/bot{settings.GROUP}/answerCallbackQuery?callback_query_id={callback_query_id}&'
        f'{encoded}&show_alert={show_alert}'
    )


def get_chat(chat_id) -> dict:
    return json.loads(
        fast_req.get(f'https://api.telegram.org/bot{settings.GROUP}/getChat?chat_id={chat_id}')['body']
    ).get('result', f'Bot was kicked out of {chat_id} group !')


def get_chat_administrators(chat_id):
    return json.loads(
        fast_req.get(f'https://api.telegram.org/bot{settings.GROUP}/getChatAdministrators?chat_id={chat_id}')['body']
    ).get('result', f'Bot was kicked out of {chat_id} !')


def entity(entity_type, *args):
    total_len = 0
    for i in args:
        if i:
            total_len += len(i)
    entities = {
        'bold': '<b>{0}</b>',
        'italic': '<i>{0}</i>',
        'text_link': '<a href="{1}">{0}</a>',
        'text_mention': '<a href="tg://user?id={1}">{0}</a>',
        'code': '<code>{0}</code>',
        'pre':  '<pre>{0}</pre>',
        'strikethrough': '<s>{0}</s>',
        'underline': '<u>{0}</u>'
    }
    return entities[entity_type].format(*args)


def clear_name(name):
    return name.replace('(', '').replace(')', '').replace('[', '').replace(']', '')


def tehran_time(current_time):
    return current_time + datetime.timedelta(hours=4, minutes=30)
