import faster_than_requests as fast_req
import json
from django.conf import settings
from anonymous import models
from django.db.models import Q
from urllib.parse import urlencode


def get_users_count():
    return models.User.objects.count()


def change_user_status(chat_id, status):
    models.User.objects.filter(chat_id=chat_id).update(status=status)


def recent_message(user, /, *, chat_id: int = None):
    if chat_id:
        messages = models.Message.objects.filter((Q(sender__chat_id=chat_id) | Q(receiver__chat_id=chat_id)))
    else:
        messages = models.Message.objects.all()
    for message in messages[:10]:
        user.send_message(f'Sender: {message.sender}\nReceiver: {message.receiver}\n\nMessage:\n{message.text}')


def recent_message_user(user):
    for message in models.Message.objects.filter(
            Q(sender__chat_id=user.database.chat_id) | Q(receiver__chat_id=user.database.chat_id)
    )[:10]:
        if message.sender == user.database:
            user.send_message(f'پیام را به {message.receiver.nick_name} ارسال کرده اید.\n\nمتن پیام:\n{message.text}')
        else:
            user.send_message(f'شما پاسخ {message.sender.nick_name} را دریافت کرده اید.\n\nمتن پیام:\n{message.text}')


def get_chat_member(chat_id, user_id: int):
    if (result := json.loads(fast_req.get(
            f'https://api.telegram.org/bot{settings.ANONYMOUS}/getChatMember?chat_id={chat_id}&user_id={user_id}'
    )['body']))['ok']:
        return result['result']


def get_chat(chat_id) -> dict:
    return json.loads(
        fast_req.get(f'https://api.telegram.org/bot{settings.ANONYMOUS}/getChat?chat_id={chat_id}')['body']
    ).get('result', f'Bot was kicked out of {chat_id} group !')


def answer_callback_query(query_id, text, show_alert):
    encoded = urlencode({'text': text})
    fast_req.get(
        f'https://api.telegram.org/bot{settings.ANONYMOUS}/answerCallbackQuery?callback_query_id={query_id}&{encoded}&'
        f'show_alert={show_alert}'
    )
